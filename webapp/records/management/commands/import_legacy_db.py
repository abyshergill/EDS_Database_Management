"""Import records from the desktop application's SQLite database (data/eds.db).

    python manage.py import_legacy_db ../data/eds.db

Images stored as BLOBs are written to media storage. Users are NOT imported:
the desktop app stored unsalted SHA-256 hashes, so accounts must be recreated
by an administrator. `created_by` is matched to an existing web user with the
same username when possible.
"""
import io
import sqlite3
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from records.models import EDSRecord, RecordHistory

FORMAT_EXT = {"JPEG": ".jpg", "PNG": ".png", "BMP": ".bmp", "GIF": ".gif", "TIFF": ".tif", "WEBP": ".webp"}


def _image_file(blob, stem):
    if not blob:
        return None
    try:
        fmt = Image.open(io.BytesIO(blob)).format
    except (UnidentifiedImageError, OSError):
        return None
    return ContentFile(bytes(blob), name=f"{stem}{FORMAT_EXT.get(fmt, '.png')}")


class Command(BaseCommand):
    help = "Import EDS records from the legacy desktop SQLite database."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the legacy eds.db file")

    def handle(self, *args, path, **options):
        db_path = Path(path)
        if not db_path.is_file():
            raise CommandError(f"File not found: {db_path}")

        User = get_user_model()
        users = {u.username: u for u in User.objects.all()}
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT rowid, component, vhx_remark, vhx_data, eds_remark, eds_data, "
                "remark, created_by FROM eds ORDER BY rowid"
            ).fetchall()
        except sqlite3.Error as exc:
            raise CommandError(f"Could not read legacy table 'eds': {exc}") from exc
        finally:
            conn.close()

        imported = skipped_images = 0
        for legacy_id, component, vhx_remark, vhx_data, eds_remark, eds_data, remark, created_by in rows:
            with transaction.atomic():
                user = users.get(created_by)
                record = EDSRecord(
                    component=(component or "").strip() or f"Legacy #{legacy_id}",
                    vhx_remark=vhx_remark or "",
                    eds_remark=eds_remark or "",
                    remark=remark or "",
                    created_by=user,
                    modified_by=user,
                )
                for field, blob in (("vhx_image", vhx_data), ("eds_image", eds_data)):
                    f = _image_file(blob, f"legacy_{legacy_id}_{field}")
                    if f:
                        getattr(record, field).save(f.name, f, save=False)
                    elif blob:
                        skipped_images += 1
                record.save()
                RecordHistory.objects.create(
                    record=record,
                    record_ref=record.pk,
                    component=record.component,
                    action=RecordHistory.Action.CREATE,
                    user=user,
                    username=created_by or "legacy-import",
                    changes={"imported_from": {"old": None, "new": f"desktop rowid {legacy_id}"}},
                )
                imported += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {imported} record(s)."))
        if skipped_images:
            self.stdout.write(self.style.WARNING(f"Skipped {skipped_images} unreadable image(s)."))
