import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse


def _upload_path(kind, filename):
    ext = Path(filename).suffix.lower() or ".png"
    return f"eds_images/{kind}/{uuid.uuid4().hex}{ext}"


def upload_vhx(instance, filename):
    return _upload_path("vhx", filename)


def upload_eds(instance, filename):
    return _upload_path("eds", filename)


class EDSRecord(models.Model):
    """One EDS analysis entry (replaces the `eds` table of the desktop app)."""

    component = models.CharField(max_length=255, db_index=True)
    vhx_image = models.ImageField("VHX image", upload_to=upload_vhx, blank=True)
    vhx_remark = models.TextField("VHX remark", blank=True)
    eds_image = models.ImageField("EDS image", upload_to=upload_eds, blank=True)
    eds_remark = models.TextField("EDS remark", blank=True)
    remark = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="records_created",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="records_modified",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # Fields tracked in the history log (images handled separately).
    TRACKED_FIELDS = ("component", "vhx_remark", "eds_remark", "remark")
    IMAGE_FIELDS = ("vhx_image", "eds_image")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "EDS record"

    def __str__(self):
        return f"#{self.pk} {self.component}"

    def get_absolute_url(self):
        return reverse("records:detail", args=[self.pk])


class RecordHistory(models.Model):
    """Audit trail entry for a create / update / delete of an EDSRecord.

    `record` is nulled when the record is deleted, but `record_ref` and
    `component` keep the history readable afterwards.
    """

    class Action(models.TextChoices):
        CREATE = "create", "Created"
        UPDATE = "update", "Updated"
        DELETE = "delete", "Deleted"

    record = models.ForeignKey(
        EDSRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history",
    )
    record_ref = models.PositiveIntegerField(db_index=True)
    component = models.CharField(max_length=255)
    action = models.CharField(max_length=10, choices=Action.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="record_history",
    )
    username = models.CharField(max_length=150)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    # {"field": {"old": ..., "new": ...}}
    changes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        verbose_name_plural = "record history"

    def __str__(self):
        return f"{self.get_action_display()} #{self.record_ref} by {self.username}"
