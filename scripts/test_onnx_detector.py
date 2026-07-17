import argparse
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from bts_monitoring.services.inference.factory import (
    get_fire_smoke_detector,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image",
        required=True,
        help="Path to input image",
    )

    parser.add_argument(
        "--output",
        default="output.jpg",
        help="Path to annotated output image",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    image_path = Path(args.image)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    frame = cv2.imread(str(image_path))

    if frame is None:
        raise RuntimeError(
            f"Could not read image: {image_path}"
        )

    detector = get_fire_smoke_detector()

    detections = detector.predict(frame)

    for detection in detections:
        if detection.bbox is None:
            continue

        x1, y1, x2, y2 = detection.bbox

        point1 = (
            int(round(x1)),
            int(round(y1)),
        )

        point2 = (
            int(round(x2)),
            int(round(y2)),
        )

        cv2.rectangle(
            frame,
            point1,
            point2,
            (0, 255, 0),
            2,
        )

        label = (
            f"{detection.class_name} "
            f"{detection.confidence:.2f}"
        )

        cv2.putText(
            frame,
            label,
            (
                point1[0],
                max(20, point1[1] - 10),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        print(
            {
                "class_id": detection.class_id,
                "class_name": detection.class_name,
                "confidence": detection.confidence,
                "bbox": detection.bbox,
                "attributes": detection.attributes,
            }
        )

    output_path = Path(args.output)

    success = cv2.imwrite(
        str(output_path),
        frame,
    )

    if not success:
        raise RuntimeError(
            f"Could not write output: {output_path}"
        )

    print(f"Saved output to: {output_path}")


if __name__ == "__main__":
    main()