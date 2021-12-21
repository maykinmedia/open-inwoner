import datetime

from django.forms import Form
from django.utils import timezone

from freezegun import freeze_time
from typeguard import check_type

from ..types.messagetype import MessageKind, MessageType
from .abstract import InclusionTagWebTest


class TestListItem(InclusionTagWebTest):
    library = "messages_tags"
    tag = "messages"
    config = {
        "message_list": [
            {
                "sender": {
                    "sender_id": "sender-1",
                    "display_name": "me",
                },
                "message_id": "message-1",
                "sent_datetime": timezone.now() - datetime.timedelta(days=2),
                "kind": MessageKind.TEXT,
                "data": "Lorem ipsum.",
            },
            {
                "sender": {
                    "sender_id": "sender-1",
                    "display_name": "me",
                },
                "message_id": "message-2",
                "sent_datetime": timezone.now() - datetime.timedelta(days=1),
                "kind": MessageKind.TEXT,
                "data": "Dolor sit amet.",
            },
            {
                "sender": {
                    "sender_id": "sender-2",
                    "display_name": "other user",
                },
                "message_id": "message-3",
                "sent_datetime": timezone.now(),
                "kind": MessageKind.TEXT,
                "data": "Consectetur adipiscing elit.",
            },
        ],
        "my_sender_id": "sender-1",
        "form": Form(),
        "subject": "Lorem ipsum.",
        "status": "Dolor sit amet.",
    }

    def test_render(self):
        self.assertRender(
            {
                "message_list": [],
                "my_sender_id": "sender-1",
                "form": Form(),
                "subject": "Lorem ipsum.",
                "status": "Dolor sit amet.",
            }
        )

    def test_message_list(self):
        check_type(
            "config['message_list']", self.config["message_list"], list[MessageType]
        )
        messages = self.assertSelector(".message", self.config)
        self.assertEqual(len(messages), 3)

    @freeze_time("2021-12-21")
    def test_message_day_headers(self):
        day_headers = self.assertSelector(".messages__day-header", self.config)
        self.assertEqual(day_headers[0].text.strip(), "19 december 2021")
        self.assertEqual(day_headers[1].text.strip(), "Gisteren")
        self.assertEqual(day_headers[2].text.strip(), "Vandaag")

    def test_message_days(self):
        self.assertTextContent(
            ".messages__day:nth-child(1) .message .message__body",
            "Lorem ipsum.",
            self.config,
        )
        self.assertTextContent(
            ".messages__day:nth-child(2) .message .message__body",
            "Dolor sit amet.",
            self.config,
        )
        self.assertTextContent(
            ".messages__day:nth-child(3) .message .message__body",
            "Consectetur adipiscing elit.",
            self.config,
        )

    def test_my_sender_id(self):
        self.assertSelector("#message-1.message--ours", self.config)
        self.assertSelector("#message-2.message--ours", self.config)
        self.assertSelector("#message-3.message--theirs", self.config)

    def test_subject(self):
        self.assertTextContent(".messages__header .h4", "Lorem ipsum.", self.config)

    def test_status(self):
        self.assertTextContent(".messages__header .p", "Dolor sit amet.", self.config)
