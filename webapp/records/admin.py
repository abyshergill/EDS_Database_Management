from django.contrib import admin

from .models import EDSRecord, RecordHistory


@admin.register(EDSRecord)
class EDSRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "component", "created_by", "created_at", "modified_by", "modified_at")
    search_fields = ("component", "remark")
    list_filter = ("created_at",)


@admin.register(RecordHistory)
class RecordHistoryAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "action", "record_ref", "component", "username")
    list_filter = ("action", "timestamp")
    search_fields = ("component", "username")

    # The audit trail is read-only, even in Django admin.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
