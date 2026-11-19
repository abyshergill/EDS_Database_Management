from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from records.models import EDSRecord

User = get_user_model()
PASSWORD = "S3cure-pass!"


class AccountTestBase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("root", password=PASSWORD, is_staff=True)
        self.user = User.objects.create_user("alice", password=PASSWORD)


class NoSelfRegistrationTests(AccountTestBase):
    def test_no_public_registration_url(self):
        self.assertEqual(self.client.get("/register/").status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/register/").status_code, 404)

    def test_anonymous_cannot_create_account(self):
        resp = self.client.post(
            reverse("accounts:create"),
            {"username": "mallory", "password1": "Very-long-pass-123", "password2": "Very-long-pass-123"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith(reverse("login")))
        self.assertFalse(User.objects.filter(username="mallory").exists())


class NormalUserRestrictionsTests(AccountTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_user_management_pages_forbidden(self):
        urls = [
            reverse("accounts:list"),
            reverse("accounts:create"),
            reverse("accounts:update", args=[self.admin.pk]),
            reverse("accounts:password", args=[self.admin.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_cannot_create_account(self):
        resp = self.client.post(
            reverse("accounts:create"),
            {"username": "mallory", "password1": "Very-long-pass-123", "password2": "Very-long-pass-123"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(User.objects.filter(username="mallory").exists())

    def test_cannot_promote_self(self):
        resp = self.client.post(
            reverse("accounts:update", args=[self.user.pk]),
            {"username": "alice", "is_staff": "on", "is_active": "on"},
        )
        self.assertEqual(resp.status_code, 403)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)

    def test_cannot_delete_or_reset_others(self):
        self.assertEqual(self.client.post(reverse("accounts:delete", args=[self.admin.pk])).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse("accounts:password", args=[self.admin.pk]),
                {"new_password1": "Another-pass-987", "new_password2": "Another-pass-987"},
            ).status_code,
            403,
        )
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(PASSWORD))

    def test_cannot_use_django_admin(self):
        resp = self.client.get("/django-admin/")
        self.assertEqual(resp.status_code, 302)  # bounced to the admin login

    def test_sidebar_hides_admin_links(self):
        resp = self.client.get(reverse("records:list"))
        self.assertNotContains(resp, reverse("accounts:list"))
        self.assertNotContains(resp, reverse("records:activity"))

    def test_can_change_own_password(self):
        resp = self.client.post(
            reverse("password_change"),
            {"old_password": PASSWORD, "new_password1": "Brand-new-pass-42", "new_password2": "Brand-new-pass-42"},
        )
        self.assertRedirects(resp, reverse("records:list"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Brand-new-pass-42"))


class AdminUserManagementTests(AccountTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_list_users(self):
        resp = self.client.get(reverse("accounts:list"))
        self.assertContains(resp, "alice")
        self.assertContains(resp, "root")

    def test_sidebar_shows_admin_links(self):
        resp = self.client.get(reverse("records:list"))
        self.assertContains(resp, reverse("accounts:list"))
        self.assertContains(resp, reverse("records:activity"))

    def test_create_normal_user_who_can_then_log_in(self):
        resp = self.client.post(
            reverse("accounts:create"),
            {"username": "carol", "first_name": "Carol", "password1": "Very-long-pass-123", "password2": "Very-long-pass-123"},
        )
        self.assertRedirects(resp, reverse("accounts:list"))
        carol = User.objects.get(username="carol")
        self.assertFalse(carol.is_staff)
        self.client.logout()
        self.assertTrue(self.client.login(username="carol", password="Very-long-pass-123"))

    def test_create_admin_user(self):
        self.client.post(
            reverse("accounts:create"),
            {"username": "dave", "is_staff": "on", "password1": "Very-long-pass-123", "password2": "Very-long-pass-123"},
        )
        self.assertTrue(User.objects.get(username="dave").is_staff)

    def test_create_rejects_weak_or_mismatched_password(self):
        for p1, p2 in (("123456", "123456"), ("Very-long-pass-123", "Different-pass-456")):
            with self.subTest(p1=p1):
                resp = self.client.post(reverse("accounts:create"), {"username": "eve", "password1": p1, "password2": p2})
                self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="eve").exists())

    def test_create_rejects_duplicate_username(self):
        resp = self.client.post(
            reverse("accounts:create"),
            {"username": "alice", "password1": "Very-long-pass-123", "password2": "Very-long-pass-123"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(username="alice").count(), 1)

    def test_promote_and_deactivate_user(self):
        resp = self.client.post(
            reverse("accounts:update", args=[self.user.pk]),
            {"username": "alice", "email": "alice@example.com", "is_staff": "on"},
        )
        self.assertRedirects(resp, reverse("accounts:list"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.client.login(username="alice", password=PASSWORD))

    def test_admin_cannot_demote_or_deactivate_self(self):
        resp = self.client.post(reverse("accounts:update", args=[self.admin.pk]), {"username": "root", "is_active": "on"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "cannot remove your own administrator rights")
        resp = self.client.post(reverse("accounts:update", args=[self.admin.pk]), {"username": "root", "is_staff": "on"})
        self.assertContains(resp, "cannot deactivate your own account")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff and self.admin.is_active)

    def test_reset_password(self):
        resp = self.client.post(
            reverse("accounts:password", args=[self.user.pk]),
            {"new_password1": "Another-pass-987", "new_password2": "Another-pass-987"},
        )
        self.assertRedirects(resp, reverse("accounts:list"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Another-pass-987"))

    def test_delete_user_keeps_their_records(self):
        record = EDSRecord.objects.create(component="Kept", created_by=self.user)
        resp = self.client.post(reverse("accounts:delete", args=[self.user.pk]))
        self.assertRedirects(resp, reverse("accounts:list"))
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        record.refresh_from_db()
        self.assertIsNone(record.created_by)

    def test_admin_cannot_delete_self(self):
        self.client.post(reverse("accounts:delete", args=[self.admin.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_admin_can_also_do_record_crud(self):
        self.client.post(reverse("records:create"), {"component": "Admin part"})
        self.assertTrue(EDSRecord.objects.filter(component="Admin part", created_by=self.admin).exists())
