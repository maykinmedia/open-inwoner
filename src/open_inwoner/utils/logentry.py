import logging

from django.contrib.admin import models
from django.utils.encoding import force_str
from django.utils.text import get_text_list
from django.utils.translation import ugettext_lazy as _

from timeline_logger.models import TimelineLog


LOG_ACTIONS = {
    models.ADDITION: (models.ADDITION, "Addition"),
    models.CHANGE: (models.CHANGE, "Change"),
    models.DELETION: (models.DELETION, "Deletion"),
    4: (4, "User action"),
}

logger = logging.getLogger(__name__)


def get_change_message(fields):
    """
    Create a change message for *fields* (a sequence of field names).
    """
    return _("Changed {changed_fields}.").format(
        changed_fields=get_text_list(fields, _("and"))
    )


def addition(request, object, message=""):
    """
    Log that an object has been successfully added.
    """
    logger.info(
        ("Added: {object}, {message}. \n{request}").format(
            object=object, message=message, request=request
        )
    )
    TimelineLog.log_from_request(
        request=request,
        content_object=object,
        # extra data
        content_object_repr=force_str(object),
        action_flag=LOG_ACTIONS[models.ADDITION],
        message=message,
    )


def change(request, object, message_or_fields):
    """
    Log that an object has been successfully changed.

    The argument *message_or_fields* must be a sequence of modified field names
    or a custom change message.
    """
    if isinstance(message_or_fields, str):
        message = message_or_fields
    else:
        message = get_change_message(message_or_fields)
    logger.info(
        ("Changed: {object}, {message}. \n{request}").format(
            object=object, message=message, request=request
        )
    )
    TimelineLog.log_from_request(
        request=request,
        content_object=object,
        # extra data
        content_object_repr=force_str(object),
        action_flag=LOG_ACTIONS[models.CHANGE],
        message=message,
    )


def deletion(request, object, message=""):
    """
    Log that an object was deleted.
    """
    logger.info(
        ("Deleted: {object}, {message}. \n{request}").format(
            object=object, message=message, request=request
        )
    )
    TimelineLog.log_from_request(
        request=request,
        content_object=object,
        # extra data
        content_object_repr=force_str(object),
        action_flag=LOG_ACTIONS[models.DELETION],
        message=message,
    )


def user_action(request, object, message):
    """
    Log a generic action done by a user, useful for when add/change/delete
    aren't appropriate.
    """
    logger.info(
        ("User action: {object}, {message}. \n{request}").format(
            object=object, message=message, request=request
        )
    )
    TimelineLog.log_from_request(
        request=request,
        content_object=object,
        # extra data
        content_object_repr=force_str(object),
        message=message,
        action_flag=LOG_ACTIONS[4],
    )


def system_action(message, object=None, user=None, log_level=None):
    """
    Log a generic action done by business logic. ``User`` instance in the log
    will be a randomly selected superuser if not specified
    """
    logger.info(
        ("System action: {object}, {message}. \n").format(
            object=object, message=message
        )
    )
    TimelineLog.objects.create(
        content_object=object,
        user=user,
        extra_data={
            "content_object_repr": force_str(object) if object else "",
            "action_flag": LOG_ACTIONS[4],
            "message": message,
            "log_level": log_level,
        },
    )


def action(message, object=None, user=None):
    """
    Log a generic action when request is not specified
    """
    logger.info(
        ("System action: {object}, {message}. \n").format(
            object=object, message=message
        )
    )
    TimelineLog.objects.create(
        content_object=object,
        user=user,
        extra_data={
            "content_object_repr": force_str(object) if object else "",
            "action_flag": LOG_ACTIONS[4],
            "message": message,
        },
    )


class LogMixin(object):
    """
    Class based views mixin that adds simple wrappers to
    the functions above.
    """

    def log_addition(self, instance, message=""):
        """
        Log that an object has been successfully added.
        """
        addition(self.request, instance, message)

    def log_change(self, instance, message_or_fields):
        """
        Log that an object has been successfully changed.
        """
        change(self.request, instance, message_or_fields)

    def log_deletion(self, instance, message):
        """
        Log that an object will be deleted.
        """
        deletion(self.request, instance, message)

    def log_user_action(self, instance, message):
        """
        Log that the current user has done something interesting.
        """
        user_action(self.request, instance, message)

    def log_system_action(self, message, instance):
        """
        Log system events not related to a specific user.
        """
        system_action(message, instance)
