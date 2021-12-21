import datetime
from typing import Union

from django import template
from django.forms import Form
from django.utils import timezone
from django.utils.translation import gettext as _

from ..types.messagetype import MessageKind, MessageType

register = template.Library()


@register.inclusion_tag("components/Messages/Messages.html")
def messages(
    message_list: list[MessageType],
    my_sender_id: str,
    form: Form,
    subject: str,
    status: str,
):
    def get_dates(message_list: list[MessageType]) -> list[datetime.date]:
        """
        Returns a list of dates to render message(s) for.
        """
        dates = sorted(set([m["sent_datetime"].date() for m in message_list]))
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

    def get_messages_by_date(message_list) -> list[dict]:
        """
        Returns a dict containing the date, it's text value and the messages sent on that date.
        """

        dates = get_dates(message_list)
        return [
            {
                "date": d,
                "text": get_date_text(d),
                "messages": sorted(
                    [m for m in message_list if m["sent_datetime"].date() == d],
                    key=lambda m: m["sent_datetime"],
                ),
            }
            for d in dates
        ]

    return {
        "days": get_messages_by_date(message_list),
        "form": form,
        "my_sender_id": my_sender_id,
        "status": status,
        "subject": subject,
    }


@register.inclusion_tag("components/Messages/Message.html")
def message(message_dict: MessageType, ours: bool) -> dict:
    return {
        "ours": ours,
        "message": message_dict,
        "message_content": message_dict["data"]
        if message_dict["kind"] == MessageKind.TEXT
        else None,
    }
