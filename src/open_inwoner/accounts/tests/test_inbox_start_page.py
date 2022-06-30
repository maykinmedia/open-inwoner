from django.urls import reverse, reverse_lazy

from django_webtest import WebTest
from furl import furl
from privates.test import temp_private_root

from ..models import Message
from .factories import ContactFactory, DocumentFactory, UserFactory


class InboxPageTests(WebTest):
    url = reverse_lazy("accounts:inbox_start")

    def setUp(self) -> None:
        super().setUp()

        self.me = UserFactory.create()
        self.app.set_user(self.me)

    def test_contact_choices_include_only_active_contacts(self):
        other_user = UserFactory.create()
        contact1 = ContactFactory.create(
            created_by=self.me,
            contact_user=other_user,
            first_name=other_user.first_name,
            last_name=other_user.last_name,
            email=other_user.email,
        )
        ContactFactory.create(created_by=self.me, contact_user__is_active=False)
        ContactFactory.create(created_by=self.me, contact_user=None)

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)

        receiver_choices = response.context["form"].fields["receiver"].choices
        self.assertEqual(
            receiver_choices,
            [[contact1.email, f"{contact1.first_name} {contact1.last_name}"]],
        )

    def test_send_message(self):
        other_user = UserFactory.create()
        contact = ContactFactory.create(
            created_by=self.me, contact_user=other_user, email=other_user.email
        )

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)

        form = response.forms["start-message-form"]
        form["receiver"] = contact.email
        form["content"] = "some message"

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            furl(reverse("accounts:inbox")).add({"with": contact.email}).url
            + "#messages-last",
        )
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.get()

        self.assertEqual(message.content, "some message")
        self.assertEqual(message.sender, self.me)
        self.assertEqual(message.receiver, other_user)

    @temp_private_root()
    def test_send_file(self):
        other_user = UserFactory.create()
        contact = ContactFactory.create(
            created_by=self.me, contact_user=other_user, email=other_user.email
        )

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)

        form = response.forms["start-message-form"]
        form["receiver"] = contact.email
        form["file"] = ("file.txt", b"test content")

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            furl(reverse("accounts:inbox")).add({"with": contact.email}).url
            + "#messages-last",
        )
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.get()

        self.assertEqual(message.content, "")
        self.assertEqual(message.sender, self.me)
        self.assertEqual(message.receiver, other_user)

        file = message.file
        self.assertEqual(file.name, "file.txt")
        self.assertEqual(file.read(), b"test content")

    def test_send_empty_message(self):
        other_user = UserFactory.create()
        contact = ContactFactory.create(
            created_by=self.me, contact_user=other_user, email=other_user.email
        )

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)

        form = response.forms["start-message-form"]
        form["receiver"] = contact.email

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"][0],
            "Of een bericht of een bestand moet ingevuld zijn",
        )
        self.assertEqual(Message.objects.count(), 0)

    @temp_private_root()
    def test_send_init_file(self):
        other_user = UserFactory.create()
        contact = ContactFactory.create(
            created_by=self.me, contact_user=other_user, email=other_user.email
        )
        document = DocumentFactory.create(owner=self.me)
        url = furl(self.url).add({"file": document.uuid}).url

        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)

        form = response.forms["start-message-form"]
        form["receiver"] = contact.email

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            furl(reverse("accounts:inbox")).add({"with": contact.email}).url
            + "#messages-last",
        )
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.get()

        self.assertEqual(message.content, "")
        self.assertEqual(message.sender, self.me)
        self.assertEqual(message.receiver, other_user)
        self.assertEqual(message.file, document.file)
