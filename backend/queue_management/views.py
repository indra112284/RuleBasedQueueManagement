from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Alert, Counter, QueueMeasurement, VideoSource


@api_view(["GET"])
def dashboard_overview(request):
    video_sources = VideoSource.objects.order_by("id")
    measurements = QueueMeasurement.objects.select_related(
        "video_source"
    ).order_by("-measured_at")[:10]
    alerts = Alert.objects.select_related(
        "video_source"
    ).order_by("-triggered_at")[:10]
    counters = Counter.objects.order_by("name")

    return Response({
        "video_sources": [
            {
                "id": source.id,
                "name": source.name,
                "source_type": source.source_type,
                "source_path": source.source_path,
                "is_active": source.is_active,
            }
            for source in video_sources
        ],
        "recent_measurements": [
            {
                "id": item.id,
                "video_source_id": item.video_source_id,
                "video_source_name": item.video_source.name,
                "occupancy_estimate": item.occupancy_estimate,
                "is_valid": item.is_valid,
                "status": item.status,
                "measured_at": item.measured_at,
            }
            for item in measurements
        ],
        "recent_alerts": [
            {
                "id": item.id,
                "video_source_name": item.video_source.name,
                "alert_type": item.alert_type,
                "severity": item.severity,
                "queue_count": item.queue_count,
                "threshold": item.threshold,
                "status": item.status,
                "reason": item.reason,
                "evidence_path": item.evidence_path,
                "triggered_at": item.triggered_at,
            }
            for item in alerts
        ],
        "counters": [
            {
                "id": counter.id,
                "name": counter.name,
                "status": counter.status,
            }
            for counter in counters
        ],
    })
