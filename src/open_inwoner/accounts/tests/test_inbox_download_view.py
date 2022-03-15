from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from django_webtest import WebTest
from privates.test import temp_private_root

from .factories import MessageFactory, UserFactory


@temp_private_root()
class InboxDownloadTests(WebTest):
    def setUp(self) -> None:
        self.message = MessageFactory(
            file=SimpleUploadedFile("file.txt", b"test content"),
        )
        self.download_url = reverse("accounts:inbox_download", args=[self.message.uuid])

    def test_download_file_receiver(self):
        response = self.app.get(self.download_url, user=self.message.receiver)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/plain")
        self.assertEqual(response.content, b"test content")

    def test_download_file_sender(self):
        response = self.app.get(self.download_url, user=self.message.sender)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/plain")
        self.assertEqual(response.content, b"test content")

    def test_download_login_required(self):
        response = self.app.get(self.download_url)

        login_url = reverse("login")
        self.assertRedirects(response, f"{login_url}?next={self.download_url}")

    def test_download_not_your_message(self):
        other_user = UserFactory()

        response = self.app.get(self.download_url, user=other_user, status=403)
