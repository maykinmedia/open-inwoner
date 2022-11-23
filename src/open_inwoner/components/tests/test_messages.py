import datetime

from django.utils import timezone

from freezegun import freeze_time

from ...accounts.forms import InboxForm
from ...accounts.models import Message
from ...accounts.tests.factories import MessageFactory, UserFactory
from .abstract import InclusionTagWebTest


@freeze_time("2021-12-21 12:00:00")
class TestListItem(InclusionTagWebTest):
    library = "messages_tags"
    tag = "messages"

    def setUp(self) -> None:
        self.me = UserFactory.create(
            first_name="My", last_name="User", email="myuser@example.com"
        )
        self.other_user = UserFactory.create(
            first_name="Other", last_name="User", email="otheruser@example.com"
        )

        self.message_1 = MessageFactory.create(
            sender=self.me,
            receiver=self.other_user,
            created_on=timezone.now() - datetime.timedelta(days=2),
            content="Lorem ipsum.",
        )
        self.message_2 = MessageFactory.create(
            sender=self.me,
            receiver=self.other_user,
            created_on=timezone.now() - datetime.timedelta(days=1),
            content="Dolor sit amet.",
        )
        self.message_3 = MessageFactory.create(
            sender=self.other_user,
            receiver=self.me,
            created_on=timezone.now(),
            content="Consectetur adipiscing elit.",
        )
        self.message_4 = MessageFactory.create(
            sender=self.me,
            receiver=self.other_user,
            created_on=timezone.now() - datetime.timedelta(hours=2),
            content="Maecenas dignissim felis nec purus viverra.",
        )

        message_queryset = Message.objects.all()

        self.config = {
            "message_list": message_queryset,
            "me": self.me,
            "form": InboxForm(user=self.me),
            "other_user": self.other_user,
            "status": "Dolor sit amet.",
        }

    def test_render(self):
        self.assertRender(
            {
                "message_list": [],
                "me": self.me,
                "form": InboxForm(user=self.me),
                "other_user": self.other_user,
                "status": "Dolor sit amet.",
            }
        )

    def test_message_list(self):
        """
        Tests that
            - All messages passed are rendered.
        """
        messages = self.assertSelector(".message", self.config)
        self.assertEqual(len(messages), 4)

    def test_message_day_headers(self):
        """
        Tests that:
            - Dates are grouped ands sorted correctly (`get_dates()`).
            - Dates are labeled correctly (`get_date_text()`).
        """
        day_headers = self.assertSelector(".messages__day-header", self.config)
        self.assertEqual(len(day_headers), 3)
        self.assertEqual(day_headers[0].text.strip(), "19 december 2021")
        self.assertEqual(day_headers[1].text.strip(), "Gisteren")
        self.assertEqual(day_headers[2].text.strip(), "Vandaag")

    def test_message_days(self):
        """
        Tests that:
            - Messages are grouped ands sorted correctly (`get_messages_by_date()`).
        """
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
            ".messages__day:nth-child(3) .message:nth-child(1) .message__body",
            "Maecenas dignissim felis nec purus viverra.",
            self.config,
        )
        self.assertTextContent(
            ".messages__day:nth-child(3) .message:nth-child(2) .message__body",
            "Consectetur adipiscing elit.",
            self.config,
        )

    def test_my_sender_id(self):
        """
        Tests that:
            - Message tags receive the correct value for `ours`.
        """
        self.assertSelector(f"#message-{self.message_1.pk}.message--ours", self.config)
        self.assertSelector(f"#message-{self.message_2.pk}.message--ours", self.config)
        self.assertSelector(
            f"#message-{self.message_3.pk}.message--theirs", self.config
        )
        self.assertSelector(f"#message-{self.message_4.pk}.message--ours", self.config)

    def test_subject(self):
        """
        Tests that:
            - Header renders the correct subject.
        """
        self.assertTextContent(
            ".messages__header .h4", self.other_user.get_full_name(), self.config
        )

    def test_status(self):
        """
        Tests that:
            - Header renders the correct status.
        """
        self.assertTextContent(".messages__header .p", "Dolor sit amet.", self.config)
