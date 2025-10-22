from django.core.management import BaseCommand
from django.utils import timezone

import structlog

from open_inwoner.userfeed.models import FeedItemData

logger = structlog.stdlib.get_logger(__name__)


class Command(BaseCommand):
    help = "Periodically update UserFeed items that need it (use from daily cronjob)"

    def handle(self, *args, **options):
        auto_expire_items()


def auto_expire_items():
    """
    mark uncompleted auto_expiring items as completed
    """
    qs = FeedItemData.objects.filter(
        auto_expire_at__lte=timezone.now(),
        completed_at__isnull=True,
    )
    for data in qs:
        logger.info("automatically expired feed item:", id=data.id, data=data)

    qs.mark_completed()
