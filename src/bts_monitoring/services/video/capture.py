import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

import cv2
import numpy as np


FrameHandler = Callable[[np.ndarray, datetime], None]


class VideoCaptureWorker:
    def __init__(
        self,
        camera_id: str,
        stream_url: str,
        frame_handler: FrameHandler,
        target_fps: float,
    ) -> None:
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.frame_handler = frame_handler
        self.target_fps = target_fps

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name=f"capture-{self.camera_id}",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=10)

    def _run(self) -> None:
        retry_delay = 1.0

        while not self._stop_event.is_set():
            capture = cv2.VideoCapture(self.stream_url)

            if not capture.isOpened():
                capture.release()
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
                continue

            retry_delay = 1.0
            frame_interval = 1 / self.target_fps
            last_processed_at = 0.0

            try:
                while not self._stop_event.is_set():
                    success, frame = capture.read()

                    if not success:
                        break

                    now = time.monotonic()

                    if now - last_processed_at < frame_interval:
                        continue

                    last_processed_at = now

                    self.frame_handler(
                        frame,
                        datetime.now(UTC),
                    )
            finally:
                capture.release()