from django.core.management import call_command
from django.test import TestCase

from freezegun import freeze_time

from ..models import User
from .factories import UserFactory


class TestCommand(TestCase):
    @freeze_time("2021-10-01")
    def test_command_deletes_inactive_users(self):
        user = UserFactory(deactivated_on="2021-09-17", is_active=False)
        call_command("deleteinactiveusers")

        self.assertFalse(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_saves_logs_when_users_were_deleted(self):
        UserFactory(deactivated_on="2021-09-17", is_active=False)

        with self.assertLogs() as captured:
            call_command("deleteinactiveusers")

            self.assertEqual(
                captured.records[0].getMessage(), "\n1 users were successfully deleted."
            )

    @freeze_time("2021-10-01")
    def test_command_saves_logs_when_users_were_not_deleted(self):
        UserFactory(deactivated_on="2021-09-25", is_active=False)

        with self.assertLogs() as captured:
            call_command("deleteinactiveusers")

            self.assertEqual(
                captured.records[0].getMessage(), "\nNo users were deleted."
            )

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_user_if_X_days_have_not_passed(self):
        user = UserFactory(deactivated_on="2021-09-20", is_active=False)
        call_command("deleteinactiveusers")

        self.assertTrue(User.objects.filter(id=user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_staff_users(self):
        staff_user = UserFactory(
            deactivated_on="2021-09-17", is_active=False, is_staff=True
        )
        call_command("deleteinactiveusers")

        self.assertTrue(User.objects.filter(id=staff_user.id).exists())

    @freeze_time("2021-10-01")
    def test_command_does_not_delete_active_user(self):
        active_user = UserFactory()
        call_command("deleteinactiveusers")

        self.assertTrue(User.objects.filter(id=active_user.id).exists())
