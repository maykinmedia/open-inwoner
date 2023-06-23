import logging

from django.contrib.admin import models
from django.contrib.admin.utils import _get_changed_field_labels_from_form
from django.forms.fields import TypedChoiceField
from django.utils.encoding import force_str
from django.utils.text import get_text_list
from django.utils.translation import ugettext_lazy as _

from timeline_logger.models import TimelineLog

LOG_ACTIONS = {
    models.ADDITION: (models.ADDITION, "Addition"),
    models.CHANGE: (models.CHANGE, "Change"),
    models.DELETION: (models.DELETION, "Deletion"),
    4: (4, "User action"),
    5: (5, "System action"),
}

logger = logging.getLogger(__name__)


def get_change_message(fields=None, form=None):
    """
    Create a change message for *fields* (a sequence of field names).
    If *fields* are empty they can be extracted from the *form* instance
    """
    changed_fields = fields or _get_changed_field_labels_from_form(
        form, form.changed_data
    )

    return _("Changed: {changed_fields}.").format(
        changed_fields=get_text_list(changed_fields, _("and"))
    )


def get_verbose_change_message(form):
    """
    Create a change message with extended data.
    Details about the modified values are also returned.
    """
    messages = []

    for field in form.changed_data:
        updated_data = form.cleaned_data[field] or "null"
        updated_field = form.fields[field]

        # Prepare message with translated labels
        if isinstance(updated_field, TypedChoiceField):
            updated_data = dict(updated_field.choices)[updated_data]
            messages.append(
                _("{label} changed to {updated_data}.").format(
                    label=updated_field.label.capitalize(),
                    updated_data=updated_data,
                )
            )
        else:
            label = updated_field.label or field
            messages.append(
                _("{label} changed to {updated_data}.").format(
                    label=label.capitalize(), updated_data=updated_data
                )
            )
    return messages


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


def change(request, object, message):
    """
    Log that an object has been successfully changed.
    """
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


def system_action(
    message, *, content_object=None, user=None, log_level=logging.INFO, exc_info=None
):
    """
    Log a generic action done by business logic.
    """
    user_text = f"{user}: " if user else ""
    object_text = force_str(content_object) if content_object else ""

    logger.log(
        log_level,
        f"System action: {user_text}{message}. \n",
        exc_info=exc_info,
    )
    TimelineLog.objects.create(
        content_object=content_object,
        user=(None if not user or user.is_anonymous else user),
        extra_data={
            "content_object_repr": object_text,
            "action_flag": LOG_ACTIONS[5],
            "message": message,
            "log_level": log_level,
        },
    )
