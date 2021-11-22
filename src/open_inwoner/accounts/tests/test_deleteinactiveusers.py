from django.core.management import call_command
from django.test import TestCase

from freezegun import freeze_time

from ..models import User
from .factories import UserFactory


class TestCommand(TestCase):
    @freeze_time("2021-10-01")
    def test_command_deletes_inactive_regular_user_when_X_days_have_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-17", is_active=False, is_staff=False)

        with self.assertLogs() as captured:
            call_command("deleteinactiveusers")

            self.assertEqual(
                captured.records[1].getMessage(), "\n1 users were successfully deleted."
            )
            self.assertFalse(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_active_staff_user_when_X_days_have_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-17", is_active=True, is_staff=True)

        with self.assertLogs() as captured:
            call_command("deleteinactiveusers")

            self.assertEqual(
                captured.records[1].getMessage(), "\nNo users were deleted."
            )
            self.assertTrue(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_active_staff_user_when_X_days_have_not_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-25", is_active=True, is_staff=True)

        self.assertTrue(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_active_regular_user_when_X_days_have_not_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-25", is_active=True, is_staff=False)

        self.assertTrue(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_inactive_regular_user_when_X_days_have_not_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-25", is_active=False, is_staff=False)

        self.assertTrue(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_inactive_staff_user_when_X_days_have_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-17", is_active=False, is_staff=True)

        self.assertTrue(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_active_regular_user_when_X_days_have_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-17", is_active=True, is_staff=False)

        self.assertTrue(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_inactive_staff_user_when_X_days_have_not_passed(
        self,
    ):
        user = UserFactory(deactivated_on="2021-09-25", is_active=False, is_staff=True)

        self.assertTrue(User.objects.filter(id=user.id).exists())
