from __future__ import annotations

from dataclasses import dataclass


class CameraServiceError(RuntimeError):
    """Raised when the local camera cannot provide a usable frame."""


@dataclass(slots=True)
class CameraService:
    camera_index: int = 0

    def _load_cv2(self):
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise CameraServiceError("OpenCV is not installed; camera capture is unavailable.") from exc
        return cv2

    def is_available(self) -> bool:
        try:
            cv2 = self._load_cv2()
        except CameraServiceError:
            return False

        capture = cv2.VideoCapture(self.camera_index)
        try:
            return bool(capture is not None and capture.isOpened())
        finally:
            if capture is not None:
                capture.release()

    def capture_frame_bytes(self) -> bytes | None:
        cv2 = self._load_cv2()
        capture = cv2.VideoCapture(self.camera_index)
        try:
            if capture is None or not capture.isOpened():
                return None

            ok, frame = capture.read()
            if not ok or frame is None:
                return None

            encoded_ok, encoded = cv2.imencode(".jpg", frame)
            if not encoded_ok:
                raise CameraServiceError("Camera frame capture succeeded but JPEG encoding failed.")

            return encoded.tobytes()
        finally:
            if capture is not None:
                capture.release()