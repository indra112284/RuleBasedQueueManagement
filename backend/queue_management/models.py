
from django.db import models


class VideoSource(models.Model):
    class SourceType(models.TextChoices):
        VIDEO_FILE = "VIDEO_FILE", "Recorded Video"
        LIVE_CAMERA = "LIVE_CAMERA", "Live Camera"

    name = models.CharField(max_length=100)
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.VIDEO_FILE,
    )
    source_path = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Counter(models.Model):
    class OperationalStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        AVAILABLE = "AVAILABLE", "Available"
        CLOSED = "CLOSED", "Closed"
        UNKNOWN = "UNKNOWN", "Unknown"

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=OperationalStatus.choices, default=OperationalStatus.UNKNOWN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class QueueMeasurement(models.Model):
    video_source = models.ForeignKey(VideoSource, on_delete=models.PROTECT, related_name="queue_measurements")
    occupancy_estimate = models.PositiveIntegerField(null=True, blank=True)
    is_valid = models.BooleanField(default=False)
    status = models.CharField(max_length=30, default="unavailable")
    measured_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-measured_at"]
        indexes = [models.Index(fields=["video_source", "measured_at"])]

    def __str__(self):
        return f"{self.video_source.name} - {self.measured_at}"


class Alert(models.Model):
    class AlertType(models.TextChoices):
        HIGH_QUEUE = "HIGH_QUEUE", "High Queue"

    class Severity(models.TextChoices):
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"

    video_source = models.ForeignKey(VideoSource, on_delete=models.PROTECT, related_name="alerts")
    alert_type = models.CharField(max_length=30, choices=AlertType.choices, default=AlertType.HIGH_QUEUE)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.WARNING)
    queue_count = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    reason = models.TextField(blank=True)
    recommended_action = models.CharField(max_length=255, blank=True)
    evidence_path = models.CharField(max_length=500, blank=True)
    triggered_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-triggered_at"]
        indexes = [models.Index(fields=["video_source", "status", "triggered_at"])]

    def __str__(self):
        return f"{self.alert_type} - {self.triggered_at}"
