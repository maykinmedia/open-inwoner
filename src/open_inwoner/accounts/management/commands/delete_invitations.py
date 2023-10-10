from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from open_inwoner.utils.logentry import system_action

from ...models import Invite


class Command(BaseCommand):
    help = (
        "Delete contact invitations which are older than a predefined period "
        "(the default is defined in `settings.INVITE_EXPIRY_DAYS`)"
    )

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_invitations = Invite.objects.select_related("inviter").filter(
            created_on__lt=now - timedelta(days=settings.INVITE_EXPIRY_DAYS)
        )

        grouped = defaultdict(list)

        for invite in expired_invitations:
            grouped[invite.inviter].append(invite)

        for inviter, invites in grouped.items():
            invites_info = [
                f"{invite.invitee_email} (invited on {invite.created_on.strftime('%Y-%m-%d')})"
                for invite in invites
            ]
            message = f"{len(invites)} expired contact invitations from {inviter.get_full_name()} deleted"
            system_action(message, user=inviter, deleted_invitations=invites_info)

        expired_invitations.delete()
