import logging
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deletes a regular user(not staff) after X days"

    def handle(self, *args, **options):
        User = get_user_model()
        interval = date.today() - timedelta(
            days=settings.DELETE_USER_AFTER_X_DAYS_INACTIVE
        )
        logger.info(f"\nDeleting users from before {interval}")
        users_to_be_deleted = User.objects.filter(
            is_active=False,
            is_staff=False,
            deactivated_on__lte=interval,
        )

        if users_to_be_deleted:
            results = users_to_be_deleted.delete()
            num_of_deleted_users = results[1].get("accounts.User")
            logger.info(f"\n{num_of_deleted_users} users were successfully deleted.")
        else:
            logger.info(f"\nNo users were deleted.")
