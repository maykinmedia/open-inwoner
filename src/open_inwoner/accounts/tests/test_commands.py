from django.core.management import call_command
from django.test import TestCase

from freezegun import freeze_time

from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin

from ..models import Invite
from .factories import InviteFactory, UserFactory


class DeleteContactInvitationsTest(AssertTimelineLogMixin, TestCase):
    @freeze_time("2023-09-26", as_arg=True)
    def test_delete_expired_invitations(frozen_time, self):
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
            f'deleted_invitations=["{invite1.invitee_email} (invited on 2023-09-26)", "{invite2.invitee_email} (invited on 2023-09-26)"',
            log_dump,
        )
        self.assertIn(
            f'deleted_invitations=["{invite3.invitee_email} (invited on 2023-09-26)"',
            log_dump,
        )

        self.assertNotIn(f"{invite4.invitee_email}", log_dump)
