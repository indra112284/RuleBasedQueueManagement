
import cv2


class VideoProcessor:
    """Open a recorded video or a future live-camera source."""

    def __init__(self, source):
        self.source = source
        self.capture = None

    def open(self):
        """Open the configured video source."""
        self.capture = cv2.VideoCapture(self.source)

        if not self.capture.isOpened():
            self.capture.release()
            self.capture = None
            raise ValueError(f"Could not open video source: {self.source}")

        return True

    def read_frame(self):
        """Read the next frame. Return None if reading fails or ends."""
        if self.capture is None:
            raise RuntimeError("Open the video source before reading frames.")

        success, frame = self.capture.read()

        if not success:
            return None

        return frame

    def close(self):
        """Release video resources."""
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
