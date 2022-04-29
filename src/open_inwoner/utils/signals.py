import logging

from django.contrib.admin import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from timeline_logger.models import TimelineLog

from .logentry import LOG_ACTIONS

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=models.LogEntry)
def copy_log_entry_to_timeline_logger(sender, **kwargs):
    log_entry = kwargs.get("instance")
    TimelineLog.objects.create(
        timestamp=log_entry.action_time,
        object_id=log_entry.object_id,
        content_type=log_entry.content_type,
        user=log_entry.user,
        extra_data={
            "content_object_repr": log_entry.object_repr or "",
            "action_flag": LOG_ACTIONS[log_entry.action_flag],
            "message": log_entry.get_change_message(),
        },
    )
    logger.info(
        "Modified: %s, %s",
        log_entry.content_type,
        log_entry.get_change_message(),
    )
