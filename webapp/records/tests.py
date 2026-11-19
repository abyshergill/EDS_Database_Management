import io
import shutil
import sqlite3
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import EDSRecord, RecordHistory

User = get_user_model()
TEMP_MEDIA = tempfile.mkdtemp(prefix="eds_test_media_")


def png_bytes(color="red"):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


def png_upload(name="img.png", color="red"):
    return SimpleUploadedFile(name, png_bytes(color), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class BaseRecordTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user("alice", password="S3cure-pass!")
        self.other = User.objects.create_user("bob", password="S3cure-pass!")
        self.admin = User.objects.create_user("root", password="S3cure-pass!", is_staff=True)
        self.client.force_login(self.user)

    def make_record(self, user=None, **kwargs):
        defaults = {"component": "Bracket", "remark": "initial"}
        defaults.update(kwargs)
        return EDSRecord.objects.create(created_by=user or self.user, modified_by=user or self.user, **defaults)


class AuthenticationRequiredTests(BaseRecordTest):
    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        record = self.make_record()
        urls = [
            reverse("records:list"),
            reverse("records:create"),
            reverse("records:detail", args=[record.pk]),
            reverse("records:update", args=[record.pk]),
            reverse("records:image", args=[record.pk, "vhx"]),
            reverse("records:activity"),
        ]
        for url in urls:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 302)
                self.assertTrue(resp.url.startswith(reverse("login")))

    def test_anonymous_cannot_delete(self):
        self.client.logout()
        record = self.make_record()
        self.client.post(reverse("records:delete", args=[record.pk]))
        self.assertTrue(EDSRecord.objects.filter(pk=record.pk).exists())

    def test_login_page_is_public(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_login_with_valid_credentials(self):
        self.client.logout()
        resp = self.client.post(reverse("login"), {"username": "alice", "password": "S3cure-pass!"})
        self.assertRedirects(resp, reverse("records:list"))

    def test_login_with_invalid_credentials(self):
        self.client.logout()
        resp = self.client.post(reverse("login"), {"username": "alice", "password": "wrong"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)


class RecordCrudTests(BaseRecordTest):
    def test_list_and_search(self):
        self.make_record(component="Gear housing")
        self.make_record(component="Spring clip")
        resp = self.client.get(reverse("records:list"))
        self.assertContains(resp, "Gear housing")
        self.assertContains(resp, "Spring clip")
        resp = self.client.get(reverse("records:list"), {"q": "gear"})
        self.assertContains(resp, "Gear housing")
        self.assertNotContains(resp, "Spring clip")

    def test_create_record_with_images(self):
        resp = self.client.post(
            reverse("records:create"),
            {
                "component": "  Valve body  ",
                "vhx_remark": "scratches",
                "eds_remark": "Fe, Cr peaks",
                "remark": "batch 7",
                "vhx_image": png_upload("v.png"),
                "eds_image": png_upload("e.png", "blue"),
            },
        )
        record = EDSRecord.objects.get()
        self.assertRedirects(resp, record.get_absolute_url())
        self.assertEqual(record.component, "Valve body")
        self.assertEqual(record.created_by, self.user)
        self.assertTrue(record.vhx_image.name.startswith("eds_images/vhx/"))
        self.assertTrue(record.eds_image)

    def test_create_requires_component(self):
        resp = self.client.post(reverse("records:create"), {"component": "   "})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(EDSRecord.objects.count(), 0)

    def test_create_rejects_non_image(self):
        bad = SimpleUploadedFile("notes.png", b"not an image", content_type="image/png")
        resp = self.client.post(reverse("records:create"), {"component": "X", "vhx_image": bad})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(EDSRecord.objects.count(), 0)

    @override_settings(MAX_IMAGE_UPLOAD_SIZE=10)
    def test_create_rejects_oversized_image(self):
        resp = self.client.post(reverse("records:create"), {"component": "X", "vhx_image": png_upload()})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "smaller than")
        self.assertEqual(EDSRecord.objects.count(), 0)

    def test_detail_page(self):
        record = self.make_record(component="Shaft")
        resp = self.client.get(reverse("records:detail", args=[record.pk]))
        self.assertContains(resp, "Shaft")

    def test_user_can_update_record_created_by_another_user(self):
        record = self.make_record(user=self.other)
        resp = self.client.post(
            reverse("records:update", args=[record.pk]),
            {"component": "Bracket v2", "remark": "initial"},
        )
        self.assertRedirects(resp, record.get_absolute_url())
        record.refresh_from_db()
        self.assertEqual(record.component, "Bracket v2")
        self.assertEqual(record.created_by, self.other)
        self.assertEqual(record.modified_by, self.user)

    def test_update_replaces_image_and_deletes_old_file(self):
        record = self.make_record()
        record.vhx_image.save("old.png", png_upload("old.png"), save=True)
        old_path = Path(record.vhx_image.path)
        self.assertTrue(old_path.exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("records:update", args=[record.pk]),
                {"component": "Bracket", "remark": "initial", "vhx_image": png_upload("new.png", "green")},
            )
        record.refresh_from_db()
        self.assertNotEqual(Path(record.vhx_image.path), old_path)
        self.assertFalse(old_path.exists())

    def test_update_can_remove_image(self):
        record = self.make_record()
        record.eds_image.save("e.png", png_upload("e.png"), save=True)
        self.client.post(
            reverse("records:update", args=[record.pk]),
            {"component": "Bracket", "remark": "initial", "remove_eds_image": "on"},
        )
        record.refresh_from_db()
        self.assertFalse(record.eds_image)

    def test_delete_record(self):
        record = self.make_record()
        record.vhx_image.save("v.png", png_upload(), save=True)
        path = Path(record.vhx_image.path)
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(reverse("records:delete", args=[record.pk]))
        self.assertRedirects(resp, reverse("records:list"))
        self.assertFalse(EDSRecord.objects.exists())
        self.assertFalse(path.exists())

    def test_delete_requires_post(self):
        record = self.make_record()
        resp = self.client.get(reverse("records:delete", args=[record.pk]))
        self.assertEqual(resp.status_code, 405)
        self.assertTrue(EDSRecord.objects.exists())

    def test_image_view_serves_and_downloads(self):
        record = self.make_record(component="Pin")
        record.vhx_image.save("v.png", png_upload(), save=True)
        resp = self.client.get(reverse("records:image", args=[record.pk, "vhx"]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertEqual(b"".join(resp.streaming_content), record.vhx_image.open("rb").read())
        resp = self.client.get(reverse("records:image", args=[record.pk, "vhx"]), {"download": "1"})
        self.assertIn("attachment", resp["Content-Disposition"])
        self.assertIn("Pin_VHX.png", resp["Content-Disposition"])

    def test_image_view_404_when_missing_or_bad_kind(self):
        record = self.make_record()
        self.assertEqual(self.client.get(reverse("records:image", args=[record.pk, "eds"])).status_code, 404)
        self.assertEqual(self.client.get(reverse("records:image", args=[record.pk, "xyz"])).status_code, 404)


class HistoryLoggingTests(BaseRecordTest):
    def test_create_is_logged(self):
        self.client.post(reverse("records:create"), {"component": "Nozzle", "remark": "r1", "vhx_image": png_upload()})
        record = EDSRecord.objects.get()
        entry = RecordHistory.objects.get()
        self.assertEqual(entry.action, RecordHistory.Action.CREATE)
        self.assertEqual(entry.record, record)
        self.assertEqual(entry.record_ref, record.pk)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.username, "alice")
        self.assertEqual(entry.changes["component"], {"old": None, "new": "Nozzle"})
        self.assertEqual(entry.changes["vhx_image"]["new"], "uploaded")
        self.assertNotIn("eds_image", entry.changes)

    def test_update_logs_only_changed_fields_with_old_and_new(self):
        record = self.make_record(component="Lever", remark="old remark", eds_remark="keep")
        self.client.post(
            reverse("records:update", args=[record.pk]),
            {"component": "Lever", "remark": "new remark", "eds_remark": "keep", "eds_image": png_upload()},
        )
        entry = RecordHistory.objects.get(action=RecordHistory.Action.UPDATE)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.changes["remark"], {"old": "old remark", "new": "new remark"})
        self.assertEqual(entry.changes["eds_image"]["new"], "uploaded")
        self.assertNotIn("component", entry.changes)
        self.assertNotIn("eds_remark", entry.changes)

    def test_image_replace_and_remove_are_logged(self):
        record = self.make_record()
        record.vhx_image.save("a.png", png_upload(), save=True)
        record.eds_image.save("b.png", png_upload(), save=True)
        self.client.post(
            reverse("records:update", args=[record.pk]),
            {"component": "Bracket", "remark": "initial", "vhx_image": png_upload("c.png"), "remove_eds_image": "on"},
        )
        entry = RecordHistory.objects.get(action=RecordHistory.Action.UPDATE)
        self.assertEqual(entry.changes["vhx_image"]["new"], "replaced")
        self.assertEqual(entry.changes["eds_image"]["new"], "removed")

    def test_noop_update_is_not_logged(self):
        record = self.make_record()
        resp = self.client.post(
            reverse("records:update", args=[record.pk]), {"component": "Bracket", "remark": "initial"}, follow=True
        )
        self.assertContains(resp, "No changes were made")
        self.assertFalse(RecordHistory.objects.filter(action=RecordHistory.Action.UPDATE).exists())

    def test_history_records_each_editor(self):
        self.client.post(reverse("records:create"), {"component": "Cap"})
        record = EDSRecord.objects.get()
        self.client.force_login(self.other)
        self.client.post(reverse("records:update", args=[record.pk]), {"component": "Cap", "remark": "by bob"})
        users = list(RecordHistory.objects.filter(record_ref=record.pk).order_by("id").values_list("username", "action"))
        self.assertEqual(users, [("alice", "create"), ("bob", "update")])

    def test_delete_is_logged_and_history_survives(self):
        self.client.post(reverse("records:create"), {"component": "Seal", "remark": "x"})
        record = EDSRecord.objects.get()
        pk = record.pk
        self.client.post(reverse("records:delete", args=[pk]))
        entries = RecordHistory.objects.filter(record_ref=pk).order_by("id")
        self.assertEqual([e.action for e in entries], ["create", "delete"])
        delete_entry = entries.last()
        self.assertIsNone(delete_entry.record)
        self.assertEqual(delete_entry.component, "Seal")
        self.assertEqual(delete_entry.changes["remark"], {"old": "x", "new": None})
        # create entry's FK is nulled but its reference is kept
        self.assertIsNone(entries.first().record)

    def test_history_survives_user_deletion(self):
        self.client.post(reverse("records:create"), {"component": "Clip"})
        self.user.delete()
        entry = RecordHistory.objects.get()
        self.assertIsNone(entry.user)
        self.assertEqual(entry.username, "alice")

    def test_detail_page_shows_history(self):
        self.client.post(reverse("records:create"), {"component": "Rotor", "remark": "a"})
        record = EDSRecord.objects.get()
        self.client.post(reverse("records:update", args=[record.pk]), {"component": "Rotor", "remark": "b"})
        resp = self.client.get(reverse("records:detail", args=[record.pk]))
        self.assertContains(resp, "Change history")
        self.assertContains(resp, "Created")
        self.assertContains(resp, "Updated")

    def test_failed_validation_logs_nothing(self):
        self.client.post(reverse("records:create"), {"component": ""})
        self.assertFalse(RecordHistory.objects.exists())


class ActivityLogTests(BaseRecordTest):
    def test_normal_user_forbidden(self):
        self.assertEqual(self.client.get(reverse("records:activity")).status_code, 403)

    def test_admin_can_view_and_filter(self):
        self.client.post(reverse("records:create"), {"component": "Alpha"})
        self.client.force_login(self.other)
        self.client.post(reverse("records:create"), {"component": "Beta"})
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("records:activity"))
        self.assertContains(resp, "Alpha")
        self.assertContains(resp, "Beta")
        resp = self.client.get(reverse("records:activity"), {"user": "bob"})
        self.assertNotContains(resp, "Alpha")
        self.assertContains(resp, "Beta")
        resp = self.client.get(reverse("records:activity"), {"action": "delete"})
        self.assertNotContains(resp, "#1 Alpha")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LegacyImportTests(TestCase):
    def test_import_from_desktop_database(self):
        user = User.objects.create_user("admin", password="x")
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "eds.db"
            conn = sqlite3.connect(db)
            conn.execute(
                "CREATE TABLE eds (rowid INTEGER PRIMARY KEY AUTOINCREMENT, component TEXT NOT NULL, "
                "vhx_remark TEXT, vhx_data BLOB, eds_remark TEXT, eds_data BLOB, remark TEXT, created_by TEXT, "
                "created_date TIMESTAMP, modified_date TIMESTAMP)"
            )
            conn.execute(
                "INSERT INTO eds (component, vhx_remark, vhx_data, eds_remark, eds_data, remark, created_by) "
                "VALUES (?,?,?,?,?,?,?)",
                ("Housing", "v", png_bytes(), "e", None, "r", "admin"),
            )
            conn.execute(
                "INSERT INTO eds (component, vhx_data, created_by) VALUES (?,?,?)",
                ("Orphan", b"garbage", "ghost"),
            )
            conn.commit()
            conn.close()
            out = io.StringIO()
            call_command("import_legacy_db", str(db), stdout=out)

        self.assertIn("Imported 2", out.getvalue())
        housing = EDSRecord.objects.get(component="Housing")
        self.assertEqual(housing.created_by, user)
        self.assertTrue(housing.vhx_image.name.endswith(".png"))
        self.assertFalse(housing.eds_image)
        orphan = EDSRecord.objects.get(component="Orphan")
        self.assertIsNone(orphan.created_by)
        self.assertFalse(orphan.vhx_image)
        self.assertEqual(RecordHistory.objects.filter(action="create").count(), 2)
