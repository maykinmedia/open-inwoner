from django.core.management import call_command
from django.test import TestCase

from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from ..models import Invite
from .factories import InviteFactory, UserFactory


class DeleteContactInvitationsTest(TestCase):
    @freeze_time("2023-09-26", as_arg=True)
    def test_delete_expired_invitations(frozen_time, self):
        user = UserFactory(
            first_name="Johann Maria Salvadore",
            infix="van de",
            last_name="Eenzaameiland",
        )

        invite1 = InviteFactory.create(inviter=user)
        invite2 = InviteFactory.create(inviter=user)
        invite3 = InviteFactory.create()

        frozen_time.move_to("2023-10-01")

        invite4 = InviteFactory.create()

        frozen_time.move_to("2023-10-27")

        call_command("delete_invitations")

        # check remaining invites
        invitations = Invite.objects.all()
        self.assertEqual(len(invitations), 1)
        self.assertEqual(invitations[0].invitee_email, invite4.invitee_email)

        # check logs
        logs = TimelineLog.objects.all()
        self.assertEqual(len(logs), 2)

        self.assertEqual(
            logs[0].extra_data["deleted_invitations"][0],
            f"{invite1.invitee_email} (invited on {invite1.created_on.strftime('%Y-%m-%d')})",
        )
        self.assertEqual(
            logs[0].extra_data["deleted_invitations"][1],
            f"{invite2.invitee_email} (invited on {invite2.created_on.strftime('%Y-%m-%d')})",
        )
        self.assertEqual(
            logs[1].extra_data["deleted_invitations"][0],
            f"{invite3.invitee_email} (invited on {invite3.created_on.strftime('%Y-%m-%d')})",
        )
