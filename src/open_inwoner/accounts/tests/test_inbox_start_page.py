from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from furl import furl
from privates.test import temp_private_root
from webtest import Upload

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.tests.helpers import create_image_bytes

from ..models import Message
from .factories import DocumentFactory, UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class InboxPageTests(WebTest):
    def setUp(self) -> None:
        super().setUp()

        self.user = UserFactory.create()
        self.app.set_user(self.user)

        self.url = reverse("inbox:start")

    def test_contact_choices_include_only_active_contacts(self):
        active_contact = UserFactory()
        inactive_contact = UserFactory(is_active=False)
        self.user.user_contacts.add(active_contact, inactive_contact)

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)

        receiver_choices = response.context["form"].fields["receiver"].choices
        self.assertEqual(
            receiver_choices,
            [
                [
                    str(active_contact.uuid),
                    active_contact.get_full_name(),
                ]
            ],
        )

    def test_send_message(self):
        contact = UserFactory()
        self.user.user_contacts.add(contact)

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)

        form = response.forms["start-message-form"]
        form["receiver"] = str(contact.uuid)
        form["content"] = "some message"

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        url = reverse("inbox:index", kwargs={"uuid": contact.uuid})
        self.assertEqual(response.url, url + "#messages-last")
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.get()

        self.assertEqual(message.content, "some message")
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.receiver, contact)

    @temp_private_root()
    def test_send_file(self):
        contact = UserFactory()
        self.user.user_contacts.add(contact)

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)

        form = response.forms["start-message-form"]
        form["receiver"] = str(contact.uuid)
        form["file"] = ("file.txt", b"test content")

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        url = reverse("inbox:index", kwargs={"uuid": contact.uuid})
        self.assertEqual(response.url, url + "#messages-last")
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.get()

        self.assertEqual(message.content, "")
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.receiver, contact)

        file = message.file
        self.assertEqual(file.name, "file.txt")
        self.assertEqual(file.read(), b"test content")

    def test_send_empty_message(self):
        contact = UserFactory()
        self.user.user_contacts.add(contact)

        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)

        form = response.forms["start-message-form"]
        form["receiver"] = str(contact.uuid)

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"][0],
            "Of een bericht of een bestand moet ingevuld zijn",
        )
        self.assertEqual(Message.objects.count(), 0)

    @temp_private_root()
    def test_send_init_file(self):
        contact = UserFactory()
        self.user.user_contacts.add(contact)
        document = DocumentFactory.create(owner=self.user)
        url = furl(self.url).add({"file": document.uuid}).url

        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)

        form = response.forms["start-message-form"]
        form["receiver"] = str(contact.uuid)

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        url = reverse("inbox:index", kwargs={"uuid": contact.uuid})
        self.assertEqual(response.url, url + "#messages-last")
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.get()

        self.assertEqual(message.content, "")
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.receiver, contact)
        self.assertEqual(message.file, document.file)

    def test_send_empty_message_with_sharing_disabled(self):
        contact = UserFactory()
        self.user.user_contacts.add(contact)
        config = SiteConfiguration.get_solo()
        config.allow_messages_file_sharing = False
        config.save()

        response = self.app.get(self.url)
        form = response.forms["start-message-form"]
        form["receiver"] = str(contact.uuid)
        response = form.submit()

        expected_error = {"content": [_("Content should be filled in")]}

        self.assertEqual(response.context["form"].errors, expected_error)

    def test_file_is_not_rendered_when_sharing_not_allowed(self):
        config = SiteConfiguration.get_solo()
        config.allow_messages_file_sharing = False
        config.save()

        response = self.app.get(self.url)
        file = response.pyquery(".message-file")

        self.assertEqual(file, [])

    def test_file_field_doesnt_exist_when_sharing_not_allowed(self):
        config = SiteConfiguration.get_solo()
        config.allow_messages_file_sharing = False
        config.save()

        response = self.app.get(self.url)
        form = response.forms["start-message-form"]

        self.assertNotIn("file", form.fields.keys())

    def test_file_cannot_be_uploaded_when_sharing_disabled(self):
        config = SiteConfiguration.get_solo()
        config.allow_messages_file_sharing = False
        config.save()

        contact = UserFactory()
        self.user.user_contacts.add(contact)

        img_bytes = create_image_bytes()
        file = Upload("test_image.png", img_bytes, "image/png")

        self.app.post(
            self.url, {"receiver": str(contact.uuid), "file": file}, status=403
        )
