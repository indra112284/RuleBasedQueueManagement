
from ultralytics import YOLO


class QueueDetector:
    """Detect people whose bounding-box centers fall inside the counter ROI."""

    def __init__(self, model_path="yolo11n.pt", confidence=0.35):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame, roi):
        if frame is None or frame.size == 0:
            raise ValueError("Frame is empty or invalid.")

        x, y, width, height = roi
        frame_height, frame_width = frame.shape[:2]

        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError("ROI coordinates and dimensions must be positive.")

        if x + width > frame_width or y + height > frame_height:
            raise ValueError("ROI extends outside the frame.")

        results = self.model.predict(
            source=frame,
            classes=[0],
            conf=self.confidence,
            verbose=False,
            device="cpu",
        )

        detections = []

        for result in results:
            for box in result.boxes:
                bx1, by1, bx2, by2 = box.xyxy[0].tolist()
                center_x = (bx1 + bx2) / 2
                center_y = (by1 + by2) / 2

                # Count a person only when their center is inside the ROI.
                if (
                    x <= center_x < x + width
                    and y <= center_y < y + height
                ):
                    detections.append({
                        "x": int(bx1),
                        "y": int(by1),
                        "width": int(bx2 - bx1),
                        "height": int(by2 - by1),
                        "confidence": float(box.conf[0]),
                    })

        return {
            "occupancy_estimate": len(detections),
            "valid": True,
            "status": "yolo_person_detection",
            "method": "yolo11n",
            "detections": detections,
        }
