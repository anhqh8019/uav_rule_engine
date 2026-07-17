from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort

from bts_monitoring.services.inference.base import (
    AIModel,
    ModelDetection,
)


@dataclass(frozen=True)
class LetterboxMetadata:
    scale: float
    pad_x: int
    pad_y: int
    original_width: int
    original_height: int
    input_width: int
    input_height: int


class OnnxYoloDetector(AIModel):
    def __init__(
        self,
        *,
        name: str,
        version: str,
        model_path: str | Path,
        class_names: list[str],
        input_size: tuple[int, int] = (640, 640),
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        providers: list[str] | None = None,
    ) -> None:
        self.name = name
        self.version = version

        self.model_path = Path(model_path).resolve()

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ONNX model not found: {self.model_path}"
            )

        if not class_names:
            raise ValueError("class_names must not be empty")

        input_width, input_height = input_size

        if input_width <= 0 or input_height <= 0:
            raise ValueError("input_size must be positive")

        if not 0 <= confidence_threshold <= 1:
            raise ValueError(
                "confidence_threshold must be between 0 and 1"
            )

        if not 0 <= iou_threshold <= 1:
            raise ValueError(
                "iou_threshold must be between 0 and 1"
            )

        self.class_names = class_names
        self.input_width = input_width
        self.input_height = input_height
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold

        available_providers = ort.get_available_providers()

        if providers is None:
            providers = self._select_default_providers(
                available_providers
            )

        unavailable = [
            provider
            for provider in providers
            if provider not in available_providers
        ]

        if unavailable:
            raise RuntimeError(
                "Requested ONNX Runtime providers are unavailable: "
                f"{unavailable}. Available: {available_providers}"
            )

        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )

        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=session_options,
            providers=providers,
        )

        inputs = self.session.get_inputs()

        if len(inputs) != 1:
            raise RuntimeError(
                f"Expected 1 model input, got {len(inputs)}"
            )

        self.input_name = inputs[0].name
        self.input_shape = inputs[0].shape
        self.output_names = [
            output.name
            for output in self.session.get_outputs()
        ]

    @staticmethod
    def _select_default_providers(
        available_providers: list[str],
    ) -> list[str]:
        selected: list[str] = []

        if "CUDAExecutionProvider" in available_providers:
            selected.append("CUDAExecutionProvider")

        selected.append("CPUExecutionProvider")

        return selected

    def predict(
        self,
        frame: np.ndarray,
    ) -> list[ModelDetection]:
        self._validate_frame(frame)

        tensor, metadata = self._preprocess(frame)

        started_at = perf_counter()

        outputs = self.session.run(
            self.output_names,
            {
                self.input_name: tensor,
            },
        )

        inference_ms = (
            perf_counter() - started_at
        ) * 1000

        detections = self._postprocess(
            outputs=outputs,
            metadata=metadata,
        )

        return [
            ModelDetection(
                class_id=detection.class_id,
                class_name=detection.class_name,
                confidence=detection.confidence,
                bbox=detection.bbox,
                polygon=detection.polygon,
                attributes={
                    **detection.attributes,
                    "inference_ms": round(inference_ms, 2),
                    "model_name": self.name,
                    "model_version": self.version,
                },
            )
            for detection in detections
        ]

    @staticmethod
    def _validate_frame(frame: np.ndarray) -> None:
        if frame is None:
            raise ValueError("frame must not be None")

        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a numpy.ndarray")

        if frame.ndim != 3:
            raise ValueError(
                "frame must have shape H x W x C"
            )

        if frame.shape[2] != 3:
            raise ValueError(
                "frame must contain exactly 3 channels"
            )

        if frame.size == 0:
            raise ValueError("frame must not be empty")

    def _preprocess(
        self,
        frame: np.ndarray,
    ) -> tuple[np.ndarray, LetterboxMetadata]:
        letterboxed, metadata = self._letterbox(frame)

        rgb = cv2.cvtColor(
            letterboxed,
            cv2.COLOR_BGR2RGB,
        )

        tensor = rgb.astype(np.float32) / 255.0

        tensor = np.transpose(
            tensor,
            (2, 0, 1),
        )

        tensor = np.expand_dims(
            tensor,
            axis=0,
        )

        tensor = np.ascontiguousarray(
            tensor,
            dtype=np.float32,
        )

        return tensor, metadata

    def _letterbox(
        self,
        frame: np.ndarray,
    ) -> tuple[np.ndarray, LetterboxMetadata]:
        original_height, original_width = frame.shape[:2]

        scale = min(
            self.input_width / original_width,
            self.input_height / original_height,
        )

        resized_width = max(
            1,
            round(original_width * scale),
        )

        resized_height = max(
            1,
            round(original_height * scale),
        )

        resized = cv2.resize(
            frame,
            (resized_width, resized_height),
            interpolation=cv2.INTER_LINEAR,
        )

        total_pad_x = self.input_width - resized_width
        total_pad_y = self.input_height - resized_height

        left = total_pad_x // 2
        right = total_pad_x - left
        top = total_pad_y // 2
        bottom = total_pad_y - top

        padded = cv2.copyMakeBorder(
            resized,
            top,
            bottom,
            left,
            right,
            borderType=cv2.BORDER_CONSTANT,
            value=(114, 114, 114),
        )

        metadata = LetterboxMetadata(
            scale=scale,
            pad_x=left,
            pad_y=top,
            original_width=original_width,
            original_height=original_height,
            input_width=self.input_width,
            input_height=self.input_height,
        )

        return padded, metadata

    def _postprocess(
        self,
        *,
        outputs: list[np.ndarray],
        metadata: LetterboxMetadata,
    ) -> list[ModelDetection]:
        if not outputs:
            return []

        predictions = np.asarray(outputs[0])

        predictions = self._normalize_output_shape(
            predictions
        )

        boxes: list[list[float]] = []
        scores: list[float] = []
        class_ids: list[int] = []

        for row in predictions:
            parsed = self._parse_prediction_row(row)

            if parsed is None:
                continue

            center_x, center_y, width, height = parsed[
                "bbox"
            ]
            class_id = parsed["class_id"]
            confidence = parsed["confidence"]

            x1 = center_x - width / 2
            y1 = center_y - height / 2
            x2 = center_x + width / 2
            y2 = center_y + height / 2

            x1, y1, x2, y2 = self._restore_bbox(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                metadata=metadata,
            )

            if x2 <= x1 or y2 <= y1:
                continue

            boxes.append(
                [
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1,
                ]
            )
            scores.append(confidence)
            class_ids.append(class_id)

        kept_indexes = self._class_aware_nms(
            boxes=boxes,
            scores=scores,
            class_ids=class_ids,
        )

        detections: list[ModelDetection] = []

        for index in kept_indexes:
            x, y, width, height = boxes[index]
            class_id = class_ids[index]

            if not 0 <= class_id < len(self.class_names):
                continue

            detections.append(
                ModelDetection(
                    class_id=class_id,
                    class_name=self.class_names[class_id],
                    confidence=float(scores[index]),
                    bbox=(
                        float(x),
                        float(y),
                        float(x + width),
                        float(y + height),
                    ),
                    attributes={},
                )
            )

        return detections

    @staticmethod
    def _normalize_output_shape(
        predictions: np.ndarray,
    ) -> np.ndarray:
        # Thường gặp:
        # YOLOv5/v7: [1, N, 5 + classes]
        # YOLOv8/v11: [1, 4 + classes, N]

        if predictions.ndim == 3:
            predictions = predictions[0]

        if predictions.ndim != 2:
            raise RuntimeError(
                "Unsupported ONNX output shape: "
                f"{predictions.shape}"
            )

        # Nếu số hàng nhỏ hơn số cột, output có khả năng là
        # [4 + classes, N], cần transpose về [N, 4 + classes].
        if predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        return predictions

    def _parse_prediction_row(
        self,
        row: np.ndarray,
    ) -> dict[str, Any] | None:
        expected_without_objectness = (
            4 + len(self.class_names)
        )

        expected_with_objectness = (
            5 + len(self.class_names)
        )

        if row.shape[0] == expected_without_objectness:
            class_scores = row[4:]
            class_id = int(np.argmax(class_scores))
            confidence = float(class_scores[class_id])

        elif row.shape[0] == expected_with_objectness:
            objectness = float(row[4])
            class_scores = row[5:]
            class_id = int(np.argmax(class_scores))
            confidence = (
                objectness
                * float(class_scores[class_id])
            )

        else:
            raise RuntimeError(
                "Unexpected prediction row size: "
                f"{row.shape[0]}. Expected "
                f"{expected_without_objectness} or "
                f"{expected_with_objectness}."
            )

        if confidence < self.confidence_threshold:
            return None

        return {
            "bbox": (
                float(row[0]),
                float(row[1]),
                float(row[2]),
                float(row[3]),
            ),
            "class_id": class_id,
            "confidence": confidence,
        }

    @staticmethod
    def _restore_bbox(
        *,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        metadata: LetterboxMetadata,
    ) -> tuple[float, float, float, float]:
        x1 = (
            x1 - metadata.pad_x
        ) / metadata.scale
        y1 = (
            y1 - metadata.pad_y
        ) / metadata.scale
        x2 = (
            x2 - metadata.pad_x
        ) / metadata.scale
        y2 = (
            y2 - metadata.pad_y
        ) / metadata.scale

        x1 = float(
            np.clip(
                x1,
                0,
                metadata.original_width - 1,
            )
        )
        y1 = float(
            np.clip(
                y1,
                0,
                metadata.original_height - 1,
            )
        )
        x2 = float(
            np.clip(
                x2,
                0,
                metadata.original_width - 1,
            )
        )
        y2 = float(
            np.clip(
                y2,
                0,
                metadata.original_height - 1,
            )
        )

        return x1, y1, x2, y2

    def _class_aware_nms(
        self,
        *,
        boxes: list[list[float]],
        scores: list[float],
        class_ids: list[int],
    ) -> list[int]:
        if not boxes:
            return []

        kept: list[int] = []

        unique_class_ids = sorted(set(class_ids))

        for class_id in unique_class_ids:
            original_indexes = [
                index
                for index, value in enumerate(class_ids)
                if value == class_id
            ]

            class_boxes = [
                boxes[index]
                for index in original_indexes
            ]

            class_scores = [
                scores[index]
                for index in original_indexes
            ]

            selected = cv2.dnn.NMSBoxes(
                bboxes=class_boxes,
                scores=class_scores,
                score_threshold=self.confidence_threshold,
                nms_threshold=self.iou_threshold,
            )

            if selected is None:
                continue

            selected_array = np.asarray(
                selected
            ).reshape(-1)

            for local_index in selected_array:
                kept.append(
                    original_indexes[int(local_index)]
                )

        return sorted(
            kept,
            key=lambda index: scores[index],
            reverse=True,
        )