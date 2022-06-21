import logging

from django.contrib.admin import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from timeline_logger.models import TimelineLog

from .logentry import LOG_ACTIONS

logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.LogEntry)
def copy_log_entry_to_timeline_logger(sender, instance, **kwargs):
    TimelineLog.objects.create(
        timestamp=instance.action_time,
        object_id=instance.object_id,
        content_type=instance.content_type,
        user=instance.user,
        extra_data={
            "content_object_repr": instance.object_repr or "",
            "action_flag": LOG_ACTIONS[instance.action_flag],
            "message": str(instance.get_change_message()),
        },
    )
    logger.info(
        "Modified: %s, %s",
        instance.content_type,
        instance.get_change_message(),
    )
