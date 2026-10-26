from django.contrib import admin
from .models import Alert, Counter, QueueMeasurement, VideoSource


@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "is_active", "created_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "source_path")


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(QueueMeasurement)
class QueueMeasurementAdmin(admin.ModelAdmin):
    list_display = ("video_source", "occupancy_estimate", "is_valid", "status", "measured_at")
    list_filter = ("is_valid", "status")
    search_fields = ("video_source__name",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("alert_type", "video_source", "queue_count", "severity", "status", "triggered_at")
    list_filter = ("alert_type", "severity", "status")
    search_fields = ("video_source__name", "reason")
