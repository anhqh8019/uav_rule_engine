from functools import lru_cache
from pathlib import Path

from bts_monitoring.core.config import get_settings
from bts_monitoring.services.inference.onnx_detector import (
    OnnxYoloDetector,
)


@lru_cache
def get_fire_smoke_detector() -> OnnxYoloDetector:
    settings = get_settings()

    project_root = Path(__file__).resolve().parents[4]

    model_path = settings.fire_smoke_model_path

    if not model_path.is_absolute():
        model_path = project_root / model_path

    return OnnxYoloDetector(
        name="fire-smoke-detector",
        version=settings.fire_smoke_model_version,
        model_path=model_path,
        class_names=[
            "fire",
            "smoke",
        ],
        input_size=(640, 640),
        confidence_threshold=(
            settings.fire_smoke_confidence_threshold
        ),
        iou_threshold=(
            settings.fire_smoke_iou_threshold
        ),
    )