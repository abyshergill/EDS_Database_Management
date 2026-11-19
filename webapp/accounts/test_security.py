"""Security tests: brute force, CSRF, SQL injection, XSS, header hardening."""
import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from records.models import EDSRecord, RecordHistory

User = get_user_model()
PASSWORD = "S3cure-pass!"
TEMP_MEDIA = tempfile.mkdtemp(prefix="eds_sec_media_")


@override_settings(LOGIN_MAX_ATTEMPTS=3, LOGIN_LOCKOUT_SECONDS=600)
class BruteForceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("alice", password=PASSWORD)
        User.objects.create_user("bob", password=PASSWORD)

    def login(self, username, password, ip="10.0.0.1"):
        return self.client.post(
            reverse("login"), {"username": username, "password": password}, REMOTE_ADDR=ip
        )

    def test_account_locked_after_max_failures_even_with_correct_password(self):
        for _ in range(3):
            self.login("alice", "wrong")
        resp = self.login("alice", PASSWORD)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Too many failed login attempts")
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_lockout_is_case_insensitive_and_from_any_ip(self):
        for i in range(3):
            self.login("ALICE", "wrong", ip=f"10.0.1.{i}")
        resp = self.login("alice", PASSWORD, ip="10.9.9.9")
        self.assertContains(resp, "Too many failed login attempts")

    def test_other_users_not_affected(self):
        for _ in range(3):
            self.login("alice", "wrong", ip="10.0.0.1")
        resp = self.login("bob", PASSWORD, ip="10.0.0.2")
        self.assertRedirects(resp, reverse("records:list"))

    def test_success_resets_counter(self):
        self.login("alice", "wrong")
        self.login("alice", "wrong")
        self.assertRedirects(self.login("alice", PASSWORD), reverse("records:list"))
        self.client.logout()
        self.login("alice", "wrong")
        self.login("alice", "wrong")
        self.assertRedirects(self.login("alice", PASSWORD), reverse("records:list"))

    def test_lockout_expires(self):
        for _ in range(3):
            self.login("alice", "wrong")
        cache.clear()  # simulates LOGIN_LOCKOUT_SECONDS elapsing
        self.assertRedirects(self.login("alice", PASSWORD), reverse("records:list"))

    def test_ip_locked_after_spraying_many_usernames(self):
        # IP limit = 4 x LOGIN_MAX_ATTEMPTS = 12
        for i in range(12):
            self.login(f"user{i}", "wrong", ip="10.6.6.6")
        resp = self.login("bob", PASSWORD, ip="10.6.6.6")
        self.assertContains(resp, "Too many failed login attempts")
        self.assertRedirects(self.login("bob", PASSWORD, ip="10.7.7.7"), reverse("records:list"))

    def test_unknown_username_also_counts(self):
        for _ in range(3):
            self.login("ghost", "x")
        self.assertContains(self.login("ghost", "x"), "Too many failed login attempts")


class CSRFTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.admin = User.objects.create_user("root", password=PASSWORD, is_staff=True)
        self.client.force_login(self.admin)
        self.record = EDSRecord.objects.create(component="Target", created_by=self.admin)

    def test_state_changing_posts_without_token_are_rejected(self):
        posts = [
            (reverse("records:create"), {"component": "Evil"}),
            (reverse("records:update", args=[self.record.pk]), {"component": "Hacked"}),
            (reverse("records:delete", args=[self.record.pk]), {}),
            (reverse("accounts:create"), {"username": "evil", "password1": "Very-long-pass-1", "password2": "Very-long-pass-1"}),
            (reverse("accounts:delete", args=[self.admin.pk]), {}),
            (reverse("logout"), {}),
        ]
        for url, data in posts:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, data).status_code, 403)
        self.record.refresh_from_db()
        self.assertEqual(self.record.component, "Target")
        self.assertFalse(User.objects.filter(username="evil").exists())
        self.assertFalse(EDSRecord.objects.filter(component="Evil").exists())

    def test_login_without_token_rejected(self):
        anon = Client(enforce_csrf_checks=True)
        resp = anon.post(reverse("login"), {"username": "root", "password": PASSWORD})
        self.assertEqual(resp.status_code, 403)

    def test_post_with_valid_token_accepted(self):
        page = self.client.get(reverse("records:create"))
        token = page.cookies["csrftoken"].value
        resp = self.client.post(reverse("records:create"), {"component": "Legit", "csrfmiddlewaretoken": token})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(EDSRecord.objects.filter(component="Legit").exists())


class SQLInjectionTests(TestCase):
    PAYLOADS = ["' OR '1'='1", "'; DROP TABLE records_edsrecord; --", '" OR 1=1 --', "%' UNION SELECT username, password FROM auth_user --"]

    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user("root", password=PASSWORD, is_staff=True)
        EDSRecord.objects.create(component="Secret part", created_by=self.admin)

    def test_record_search(self):
        self.client.force_login(self.admin)
        for payload in self.PAYLOADS:
            with self.subTest(payload=payload):
                resp = self.client.get(reverse("records:list"), {"q": payload})
                self.assertEqual(resp.status_code, 200)
                self.assertNotContains(resp, "Secret part")
        self.assertEqual(EDSRecord.objects.count(), 1)

    def test_user_and_activity_search(self):
        self.client.force_login(self.admin)
        for payload in self.PAYLOADS:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.get(reverse("accounts:list"), {"q": payload}).status_code, 200)
                self.assertEqual(
                    self.client.get(reverse("records:activity"), {"q": payload, "user": payload, "action": payload}).status_code,
                    200,
                )
        self.assertEqual(User.objects.count(), 1)

    def test_login(self):
        for payload in self.PAYLOADS[:2]:
            with self.subTest(payload=payload):
                resp = self.client.post(reverse("login"), {"username": payload, "password": payload})
                self.assertFalse(resp.wsgi_request.user.is_authenticated)
                resp = self.client.post(reverse("login"), {"username": "root", "password": payload})
                self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_injection_text_is_stored_literally(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("records:create"), {"component": self.PAYLOADS[1]})
        self.assertTrue(EDSRecord.objects.filter(component=self.PAYLOADS[1]).exists())
        self.assertEqual(EDSRecord.objects.count(), 2)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class XSSAndHeaderTests(TestCase):
    XSS = '<script>alert("x")</script><img src=x onerror=alert(1)>'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.admin = User.objects.create_user("root", password=PASSWORD, is_staff=True)
        self.client.force_login(self.admin)

    def test_record_fields_are_escaped_everywhere(self):
        self.client.post(reverse("records:create"), {"component": self.XSS, "remark": self.XSS, "vhx_remark": self.XSS})
        record = EDSRecord.objects.get()
        self.client.post(reverse("records:update", args=[record.pk]), {"component": self.XSS, "remark": "changed"})
        for url in [
            reverse("records:list"),
            reverse("records:detail", args=[record.pk]),
            reverse("records:update", args=[record.pk]),
            reverse("records:activity"),
        ]:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertNotContains(resp, "<script>alert")
                self.assertNotContains(resp, "<img src=x onerror")
                self.assertContains(resp, "&lt;script&gt;")

    def test_flash_message_is_escaped(self):
        resp = self.client.post(reverse("records:create"), {"component": self.XSS}, follow=True)
        self.assertNotContains(resp, "<script>alert")

    def test_username_escaped_in_user_list(self):
        User.objects.create_user("x<b>y", password=PASSWORD)  # usernames normally can't contain <, but be safe
        resp = self.client.get(reverse("accounts:list"))
        self.assertNotContains(resp, "x<b>y")

    def test_download_filename_cannot_inject_headers(self):
        buf = io.BytesIO()
        Image.new("RGB", (4, 4)).save(buf, "PNG")
        record = EDSRecord.objects.create(component='a"\r\nSet-Cookie: pwned=1', created_by=self.admin)
        record.vhx_image.save("v.png", SimpleUploadedFile("v.png", buf.getvalue()), save=True)
        resp = self.client.get(reverse("records:image", args=[record.pk, "vhx"]), {"download": "1"})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("Set-Cookie", resp.headers)
        self.assertNotIn("\n", resp["Content-Disposition"])
        self.assertIn('filename="a_Set-Cookie_pwned_1_VHX.png"', resp["Content-Disposition"])

    def test_security_headers(self):
        resp = self.client.get(reverse("records:list"))
        self.assertEqual(resp["X-Frame-Options"], "DENY")
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resp["Referrer-Policy"], "same-origin")

    def test_session_cookie_flags(self):
        anon = Client()
        resp = anon.post(reverse("login"), {"username": "root", "password": PASSWORD})
        cookie = resp.cookies["sessionid"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_open_redirect_after_login_blocked(self):
        cache.clear()
        anon = Client()
        resp = anon.post(
            reverse("login") + "?next=https://evil.example.com/",
            {"username": "root", "password": PASSWORD, "next": "https://evil.example.com/"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn("evil.example.com", resp.url)

    def test_history_cannot_be_modified_via_django_admin(self):
        self.admin.is_superuser = True
        self.admin.save()
        self.client.post(reverse("records:create"), {"component": "Audit"})
        entry = RecordHistory.objects.get()
        self.assertEqual(self.client.get(f"/django-admin/records/recordhistory/{entry.pk}/delete/").status_code, 403)
        self.assertEqual(self.client.get("/django-admin/records/recordhistory/add/").status_code, 403)
