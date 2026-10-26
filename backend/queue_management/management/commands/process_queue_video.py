
from django.core.management.base import BaseCommand, CommandError

from queue_management.models import VideoSource
from queue_management.services.measurement_service import MeasurementService


class Command(BaseCommand):
    help = "Process a registered video and save valid queue measurements."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-id",
            type=int,
            default=1,
            help="ID of the registered video source (default: 1).",
        )
        parser.add_argument(
            "--frame-interval",
            type=int,
            default=50,
            help="Process every Nth frame (default: 50).",
        )

    def handle(self, *args, **options):
        source_id = options["source_id"]
        frame_interval = options["frame_interval"]

        if frame_interval < 1:
            raise CommandError("--frame-interval must be at least 1.")

        if not VideoSource.objects.filter(id=source_id).exists():
            raise CommandError(f"Video source with ID {source_id} does not exist.")

        service = MeasurementService(
            source_id=source_id,
            frame_interval=frame_interval,
        )

        try:
            result = service.process_video()
        except (ValueError, FileNotFoundError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Video processing completed."))
        for key, value in result.items():
            self.stdout.write(f"{key}: {value}")
