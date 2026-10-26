from pathlib import Path

import cv2
from django.conf import settings
from django.utils import timezone

from queue_management.models import Alert, QueueMeasurement, VideoSource
from queue_management.services.queue_detector import QueueDetector
from queue_management.services.video_processor import VideoProcessor


class MeasurementService:
    """Process video, record measurements, and save alert evidence."""

    def __init__(self, source_id, roi=None, frame_interval=10, alert_threshold=3):
        self.source_id = source_id
        self.roi = roi
        self.frame_interval = max(1, frame_interval)
        self.alert_threshold = max(1, alert_threshold)

    def process_video(self):
        source = VideoSource.objects.get(id=self.source_id)

        if source.source_type != "VIDEO_FILE":
            raise ValueError("This service currently supports recorded video files only.")

        video_path = Path(source.source_path)
        if not video_path.is_absolute():
            video_path = (Path(settings.BASE_DIR).parent / video_path).resolve()

        if not video_path.is_file():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        evidence_dir = Path(settings.BASE_DIR).parent / "data" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        alerts_created = 0
        frame_number = 0
        detector = QueueDetector()

        try:
            with VideoProcessor(str(video_path)) as processor:
                while True:
                    frame = processor.read_frame()
                    if frame is None:
                        break

                    frame_number += 1
                    if frame_number % self.frame_interval != 0:
                        continue

                    height, width = frame.shape[:2]
                    roi = self.roi or (250, 200, 650, 750)
                    x, y, roi_width, roi_height = roi

                    result = detector.detect(frame, roi)
                    estimate = result["occupancy_estimate"]
                    measured_at = timezone.now()

                    QueueMeasurement.objects.create(
                        video_source=source,
                        occupancy_estimate=estimate,
                        is_valid=True,
                        status="yolo_person_detection",
                        measured_at=measured_at,
                    )
                    saved_count += 1

                    active_alerts = Alert.objects.filter(
                        video_source=source,
                        alert_type=Alert.AlertType.HIGH_QUEUE,
                        status=Alert.Status.ACTIVE,
                    )

                    if estimate >= self.alert_threshold:
                        existing_alert = active_alerts.first()

                        severity = (
                            Alert.Severity.CRITICAL
                            if estimate >= self.alert_threshold * 2
                            else Alert.Severity.WARNING
                        )

                        if existing_alert is None:
                            evidence_frame = frame.copy()

                            cv2.rectangle(
                                evidence_frame,
                                (x, y),
                                (x + roi_width, y + roi_height),
                                (0, 255, 0),
                                3,
                            )

                            for detection in result["detections"]:
                                bx = detection["x"]
                                by = detection["y"]
                                bw = detection["width"]
                                bh = detection["height"]

                                cv2.rectangle(
                                    evidence_frame,
                                    (bx, by),
                                    (bx + bw, by + bh),
                                    (0, 0, 255),
                                    2,
                                )
                                cv2.putText(
                                    evidence_frame,
                                    f'Person {detection["confidence"]:.2f}',
                                    (bx, max(20, by - 8)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6,
                                    (0, 0, 255),
                                    2,
                                )

                            timestamp = measured_at.strftime("%Y%m%d_%H%M%S_%f")
                            evidence_name = f"alert_source_{source.id}_{timestamp}.jpg"
                            evidence_file = evidence_dir / evidence_name

                            if not cv2.imwrite(str(evidence_file), evidence_frame):
                                raise OSError(f"Could not save evidence image: {evidence_file}")

                            try:
                                Alert.objects.create(
                                    video_source=source,
                                    alert_type=Alert.AlertType.HIGH_QUEUE,
                                    severity=severity,
                                    queue_count=estimate,
                                    threshold=self.alert_threshold,
                                    status=Alert.Status.ACTIVE,
                                    reason=(
                                        "YOLO detected the configured number of "
                                        "people in the counter region."
                                    ),
                                    recommended_action=(
                                        "Review the counter queue and consider "
                                        "opening another service counter."
                                    ),
                                    evidence_path=str(
                                        evidence_file.relative_to(Path(settings.BASE_DIR).parent)
                                    ).replace("\\", "/"),
                                    triggered_at=measured_at,
                                )
                            except Exception:
                                evidence_file.unlink(missing_ok=True)
                                raise

                            alerts_created += 1
                        else:
                            existing_alert.queue_count = estimate
                            existing_alert.threshold = self.alert_threshold
                            existing_alert.severity = severity
                            existing_alert.save(
                                update_fields=["queue_count", "threshold", "severity"]
                            )
                    else:
                        active_alerts.update(
                            status=Alert.Status.RESOLVED,
                            resolved_at=measured_at,
                        )
        finally:
            del detector

        return {
            "video_source": source.name,
            "frames_processed": frame_number,
            "measurements_saved": saved_count,
            "alerts_created": alerts_created,
            "alert_threshold": self.alert_threshold,
            "evidence_directory": str(evidence_dir),
            "note": (
                "Counts are YOLO person detections inside the configured ROI; "
                "they are not unique customer tracks."
            ),
        }
