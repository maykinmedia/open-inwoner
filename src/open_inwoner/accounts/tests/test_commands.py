from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from freezegun import freeze_time

from open_inwoner.accounts.models import Invite
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin

from .factories import (
    DigidUserFactory,
    DigitalAddressFactory,
    InviteFactory,
    UserFactory,
    eHerkenningUserFactory,
)


class DeleteContactInvitationsTest(AssertTimelineLogMixin, TestCase):
    def test_delete_expired_invitations(self):
        with freeze_time("2023-09-26") as frozen_time:
            user = UserFactory(
                first_name="Johann Maria Salvadore",
                infix="van de",
                last_name="Eenzaameiland",
            )

            invite1 = InviteFactory.create(inviter=user, invitee_first_name="Harry")
            invite2 = InviteFactory.create(inviter=user, invitee_first_name="Sally")
            invite3 = InviteFactory.create(invitee_first_name="Joe")

            frozen_time.move_to("2023-10-01")

            invite4 = InviteFactory.create(invitee_first_name="Jane")

            frozen_time.move_to("2023-10-27")

            call_command("delete_invitations")

            # check remaining invites
            invitations = Invite.objects.all()
            self.assertEqual(len(invitations), 1)
            self.assertEqual(invitations[0].invitee_email, invite4.invitee_email)

            # check logs (use string dump, don't rely on order of logs)
            log_dump = self.getTimelineLogDump()

            self.assertIn("total 2 timelinelogs", log_dump)

            self.assertIn(
                f'"{invite1.invitee_email} (invited on 2023-09-26)"', log_dump
            )
            self.assertIn(
                f'"{invite2.invitee_email} (invited on 2023-09-26)"', log_dump
            )
            self.assertIn(
                f'deleted_invitations=["{invite3.invitee_email} (invited on 2023-09-26)"',
                log_dump,
            )

            self.assertNotIn(f"{invite4.invitee_email}", log_dump)


class FindDuplicateEmailsTest(TestCase):
    def test_lists_emails_that_are_not_allowed_to_be_shared(self):
        # regular users with a different capitalisation of the same email
        regular = UserFactory(email="dupe@example.com")
        variant = UserFactory(email="Dupe@Example.com", is_active=False)
        # login email of one user is an additional address of another
        digid = DigidUserFactory(email="mixed@example.com")
        holder = UserFactory(email="holder@example.com")
        DigitalAddressFactory(user=holder, value="Mixed@example.com")
        # allowed: shared between DigiD/eHerkenning users only
        DigidUserFactory(email="shared@example.com", bsn="111222333")
        eHerkenningUserFactory(email="Shared@example.com")

        stdout = StringIO()
        call_command("find_duplicate_emails", stdout=stdout)

        self.assertEqual(
            stdout.getvalue().splitlines(),
            [
                f"dupe@example.com: users {regular.pk} (default, active), "
                f"{variant.pk} (default, inactive)",
                f"mixed@example.com: users {digid.pk} (digid, active), "
                f"{holder.pk} (default, active)",
                "Found 2 duplicated email(s)",
            ],
        )

    def test_no_duplicates(self):
        UserFactory(email="unique@example.com")

        stdout = StringIO()
        call_command("find_duplicate_emails", stdout=stdout)

        self.assertEqual(stdout.getvalue().splitlines(), ["No duplicated emails found"])
