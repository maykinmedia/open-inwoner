from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.config_checks.fetch_userfeed import (
    FetchUserfeedCheck,
    FetchUserfeedForm,
)
from open_inwoner.userfeed.hooks.common import simple_message
from open_inwoner.userfeed.tests.factories import FeedItemDataFactory


class FetchUserfeedCheckTests(TestCase):
    def setUp(self):
        self.check = FetchUserfeedCheck()
        self.user = UserFactory()

    def test_no_items(self):
        form = FetchUserfeedForm(data={"user": self.user.pk})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertTrue(result.success)
        self.assertIn("0 feed items found", result.message)
        self.assertEqual(result.extra["total_items"], 0)
        self.assertEqual(result.extra["raw_items_count"], 0)
        self.assertEqual(result.extra["items"], [])
        self.assertEqual(result.extra["filtered_out_types"], [])

    def test_items_found(self):
        simple_message(self.user, "Hello", title="Test message")
        # noise for another user, should not be counted
        FeedItemDataFactory(user=UserFactory())

        form = FetchUserfeedForm(data={"user": self.user.pk})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertTrue(result.success)
        self.assertIn("1 feed items found", result.message)
        self.assertEqual(result.extra["total_items"], 1)
        self.assertEqual(result.extra["raw_items_count"], 1)
        self.assertEqual(
            result.extra["items"],
            [{"type": FeedItemType.message_simple, "action_required": False}],
        )

    def test_completed_items_are_not_counted_but_still_raw(self):
        simple_message(self.user, "Hello")
        item = self.user.feeditemdata_set.get()
        item.mark_completed()

        form = FetchUserfeedForm(data={"user": self.user.pk})
        self.assertTrue(form.is_valid())

        result = self.check.run(form.cleaned_data)

        self.assertTrue(result.success)
        self.assertEqual(result.extra["total_items"], 0)
        self.assertEqual(result.extra["raw_items_count"], 1)

    def test_unexpected_error(self):
        form = FetchUserfeedForm(data={"user": self.user.pk})
        self.assertTrue(form.is_valid())

        with patch(
            "open_inwoner.userfeed.config_checks.fetch_userfeed.get_feed",
            side_effect=RuntimeError("boom"),
        ):
            result = self.check.run(form.cleaned_data)

        self.assertFalse(result.success)
        self.assertIn("Unexpected error", result.message)


class FetchUserfeedViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.user = UserFactory()
        self.target_user = UserFactory()

    def get_url(self):
        return reverse(
            "run_config_check",
            args=["accounts", "user", self.target_user.pk, "fetch_userfeed"],
        )

    def test_permission_denied_for_normal_user(self):
        self.client.force_login(self.user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_permission_denied_for_staff_user_with_model_access(self):
        staff_user = UserFactory(is_staff=True, is_superuser=False)
        staff_user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="accounts",
                content_type__model="user",
            )
        )
        self.client.force_login(staff_user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)

    def test_post_runs_check(self):
        self.client.force_login(self.superuser)

        response = self.client.post(self.get_url(), {"user": self.target_user.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 feed items found")


class FetchUserfeedStandaloneTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.target_user = UserFactory()

    def test_standalone_runs_check(self):
        self.client.force_login(self.superuser)

        url = reverse("run_config_check_standalone", args=["fetch_userfeed"])

        response = self.client.post(url, {"user": self.target_user.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 feed items found")
