"""Helpers that write RecordHistory entries.

All data changes go through these functions (called from the views inside
the same transaction as the save/delete) so that every create, update and
delete is logged with who did it and what changed.
"""
import logging

from .models import EDSRecord, RecordHistory

logger = logging.getLogger(__name__)


def snapshot(record):
    """Capture the current tracked state of a record (before modification)."""
    data = {f: getattr(record, f) for f in EDSRecord.TRACKED_FIELDS}
    for f in EDSRecord.IMAGE_FIELDS:
        data[f] = getattr(record, f).name or ""
    return data


def _log(record, action, user, changes):
    entry = RecordHistory.objects.create(
        record=record if action != RecordHistory.Action.DELETE else None,
        record_ref=record.pk,
        component=record.component,
        action=action,
        user=user,
        username=user.get_username(),
        changes=changes,
    )
    logger.info(
        "Record #%s (%s) %s by %s: %s",
        record.pk,
        record.component,
        action,
        user.get_username(),
        list(changes),
    )
    return entry


def log_create(record, user):
    changes = {
        f: {"old": None, "new": getattr(record, f)}
        for f in EDSRecord.TRACKED_FIELDS
        if getattr(record, f)
    }
    for f in EDSRecord.IMAGE_FIELDS:
        if getattr(record, f):
            changes[f] = {"old": None, "new": "uploaded"}
    return _log(record, RecordHistory.Action.CREATE, user, changes)


def log_update(record, user, before):
    """Log an update. Returns None when nothing actually changed."""
    after = snapshot(record)
    changes = {}
    for f in EDSRecord.TRACKED_FIELDS:
        if before[f] != after[f]:
            changes[f] = {"old": before[f], "new": after[f]}
    for f in EDSRecord.IMAGE_FIELDS:
        if before[f] != after[f]:
            if not after[f]:
                new = "removed"
            elif not before[f]:
                new = "uploaded"
            else:
                new = "replaced"
            changes[f] = {"old": None, "new": new}
    if not changes:
        return None
    return _log(record, RecordHistory.Action.UPDATE, user, changes)


def log_delete(record, user):
    changes = {
        f: {"old": getattr(record, f), "new": None}
        for f in EDSRecord.TRACKED_FIELDS
        if getattr(record, f)
    }
    return _log(record, RecordHistory.Action.DELETE, user, changes)
