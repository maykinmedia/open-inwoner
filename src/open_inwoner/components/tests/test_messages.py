import datetime

from django.forms import Form
from django.utils import timezone
from freezegun import freeze_time

from .abstract import InclusionTagWebTest
from ...accounts.models import Message
from ...accounts.tests.factories import UserFactory, MessageFactory


@freeze_time("2021-12-21")
class TestListItem(InclusionTagWebTest):
    library = "messages_tags"
    tag = "messages"

    def setUp(self) -> None:
        self.me = UserFactory.create(first_name='My', last_name='User', email='myuser@example.com')
        other_user = UserFactory.create(first_name='Other', last_name='User', email='otheruser@example.com')

        self.message_1 = MessageFactory.create(sender=self.me, receiver=other_user, created_on=timezone.now() - datetime.timedelta(days=2), content="Lorem ipsum.")
        self.message_2 = MessageFactory.create(sender=self.me, receiver=other_user, created_on=timezone.now() - datetime.timedelta(days=1), content="Dolor sit amet.")
        self.message_3 = MessageFactory.create(sender=other_user, receiver=self.me, created_on=timezone.now(), content="Consectetur adipiscing elit.")

        message_queryset = Message.objects.all()

        self.config = {
            "message_list": message_queryset,
            "me": self.me,
            "form": Form(),
            "subject": "Lorem ipsum.",
            "status": "Dolor sit amet.",
        }

    def test_render(self):
        self.assertRender(
            {
                "message_list": [],
                "me": self.me,
                "form": Form(),
                "subject": "Lorem ipsum.",
                "status": "Dolor sit amet.",
            }
        )

    def test_message_list(self):
        messages = self.assertSelector(".message", self.config)
        self.assertEqual(len(messages), 3)

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
        self.assertSelector(f"#message-{self.message_1.pk}.message--ours", self.config)
        self.assertSelector(f"#message-{self.message_2.pk}.message--ours", self.config)
        self.assertSelector(f"#message-{self.message_3.pk}.message--theirs", self.config)

    def test_subject(self):
        self.assertTextContent(".messages__header .h4", "Lorem ipsum.", self.config)

    def test_status(self):
        self.assertTextContent(".messages__header .p", "Dolor sit amet.", self.config)
