import datetime
from typing import List, Union

from django import template
from django.forms import Form
from django.utils import timezone
from django.utils.translation import gettext as _

from open_inwoner.accounts.models import Message, User
from open_inwoner.accounts.query import MessageQuerySet

register = template.Library()


@register.inclusion_tag("components/Messages/Messages.html")
def messages(
    message_list: MessageQuerySet,
    me: User,
    form: Form,
    other_user: str,
    status: str,
):
    """
    Generate all messages in a conversation and shows the form to add a new message

    Usage:
        {% messages message_list=messages me=request.user form=message_form other_user=other_user status="open" %}

    Variables:
        + message_list: Message[] | a list of messages that needs to be displayed.
        + me: User | currently loggedin user.
        + form: Form | a django form.
        + other_user: User | The user that we will be messaging.
        + status: string | The status below the subject.

    Extra context:
        - days: set | the message_list grouped by date.
        - subject: string | The title that will be displayed above the messages.
    """

    def get_dates(message_list: MessageQuerySet) -> List[datetime.date]:
        """
        Returns a list of dates to render message(s) for.
        """
        dates = sorted(set([m.created_on.date() for m in message_list]))
        return dates

    def get_date_text(date) -> Union[str, datetime.date]:
        """ "
        Formats a date to a text value (if required).
        """

        if date == timezone.now().date():
            return _("Vandaag")

        if date == timezone.now().date() - timezone.timedelta(days=1):
            return _("Gisteren")

        return date

    def get_messages_by_date(message_list: MessageQuerySet) -> List[dict]:
        """
        Returns a dict containing the date, it's text value and the messages sent on that date.
        """

        dates = get_dates(message_list)
        return [
            {
                "date": d,
                "text": get_date_text(d),
                "messages": sorted(
                    [m for m in message_list if m.created_on.date() == d],
                    key=lambda m: m.created_on,
                ),
            }
            for d in dates
        ]

    return {
        "days": get_messages_by_date(message_list),
        "form": form,
        "me": me,
        "status": status,
        "other_user": other_user,
        "subject": other_user.get_full_name(),
    }


@register.inclusion_tag("components/Messages/Message.html")
def message(message: Message, me: User, file=False) -> dict:
    """
    Display a message

    Usage:
        {% message message="this is a message" ours=False %}

    Variables:
        + message: string | the message that needs to be displayed.
        + me: User | currently loggedin user.
        - file: bool | If we display the file

    Extra context:
        - ours: bool | if we send the message or not.
    """
    return {"message": message, "ours": message.sender == me, "file": file}
