
from pathlib import Path

import cv2
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from queue_management.models import VideoSource
from queue_management.services.queue_detector import QueueDetector
from queue_management.services.video_processor import VideoProcessor


class Command(BaseCommand):
    help = "Render a diagnostic video showing the selected region and foreground contours."

    def add_arguments(self, parser):
        parser.add_argument("--source-id", type=int, default=2)
        parser.add_argument("--x", type=int, default=250)
        parser.add_argument("--y", type=int, default=300)
        parser.add_argument("--width", type=int, default=650)
        parser.add_argument("--height", type=int, default=650)
        parser.add_argument("--output", default="queue-diagnostic.mp4")

    def handle(self, *args, **options):
        source = VideoSource.objects.filter(
            id=options["source_id"],
            source_type="VIDEO_FILE",
        ).first()

        if source is None:
            raise CommandError("Recorded video source not found.")

        video_path = Path(source.source_path)
        if not video_path.is_absolute():
            video_path = (Path(settings.BASE_DIR).parent / video_path).resolve()

        if not video_path.is_file():
            raise CommandError(f"Video not found: {video_path}")

        output_dir = Path(settings.BASE_DIR).parent / "frontend" / "public"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / options["output"]

        roi = (
            options["x"],
            options["y"],
            options["width"],
            options["height"],
        )

        detector = QueueDetector()
        writer = None
        frames = 0
        fps_capture = cv2.VideoCapture(str(video_path))

        try:
            video_fps = fps_capture.get(cv2.CAP_PROP_FPS)
        finally:
            fps_capture.release()

        if not video_fps or video_fps <= 0:
            video_fps = 25.0

        try:
            with VideoProcessor(str(video_path)) as processor:
                while True:
                    frame = processor.read_frame()
                    if frame is None:
                        break

                    frames += 1
                    frame_height, frame_width = frame.shape[:2]
                    x, y, width, height = roi

                    if (
                        x < 0 or y < 0 or width <= 0 or height <= 0
                        or x + width > frame_width
                        or y + height > frame_height
                    ):
                        raise CommandError(
                            f"ROI {roi} is outside frame size "
                            f"{frame_width}x{frame_height}."
                        )

                    if writer is None:
                        writer = cv2.VideoWriter(
                            str(output_path),
                            cv2.VideoWriter_fourcc(*"mp4v"),
                            video_fps,
                            (frame_width, frame_height),
                        )
                        if not writer.isOpened():
                            raise CommandError("Could not create output video.")

                    result = detector.detect(frame, roi)

                    cv2.rectangle(
                        frame, (x, y), (x + width, y + height),
                        (0, 255, 0), 3,
                    )

                    for item in result["detections"]:
                        bx, by = item["x"], item["y"]
                        ex = bx + item["width"]
                        ey = by + item["height"]
                        cv2.rectangle(frame, (bx, by), (ex, ey), (0, 0, 255), 2)

                    if result["valid"]:
                        label = (
                            "Foreground regions: "
                            f"{result['occupancy_estimate']} (not people count)"
                        )
                    else:
                        label = "Detector warming up"

                    cv2.putText(
                        frame, label, (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2,
                    )
                    cv2.putText(
                        frame, f"ROI: x={x}, y={y}, w={width}, h={height}",
                        (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 255), 2,
                    )
                    writer.write(frame)
        finally:
            if writer is not None:
                writer.release()
            detector.background_subtractor = None

        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise CommandError("Diagnostic video was not created.")

        self.stdout.write(self.style.SUCCESS("Diagnostic video created."))
        self.stdout.write(f"Frames processed: {frames}")
        self.stdout.write(f"Output: {output_path}")
