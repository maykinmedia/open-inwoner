from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse_lazy

from filer.models import Image
from rest_framework import status
from rest_framework.test import APITestCase

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.test import temp_media_root


class ImageUploadPermissionsTests(APITestCase):
    url = reverse_lazy("upload_image")

    def test_no_auth(self):
        image = SimpleUploadedFile(
            "test_image.jpg", content=b"file content", content_type="image/jpeg"
        )
        response = self.client.post(self.url, {"upload": image})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_auth_but_not_staff(self):
        image = SimpleUploadedFile(
            "test_image.jpg", content=b"file content", content_type="image/jpeg"
        )
        user = UserFactory.create()
        self.client.force_login(user)

        response = self.client.post(self.url, {"upload": image})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ImageUploadApiTests(APITestCase):
    url = reverse_lazy("upload_image")

    def setUp(self) -> None:
        super().setUp()

        self.user = UserFactory.create(is_staff=True)
        self.client.force_login(self.user)

    @temp_media_root()
    def test_upload_new_file(self):
        image = SimpleUploadedFile(
            "test_image.jpg", content=b"file content", content_type="image/jpeg"
        )
        response = self.client.post(self.url, {"upload": image})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Image.objects.count(), 1)

        image = Image.objects.get()

        self.assertEqual(image.folder.name, "ckeditor")
        self.assertEqual(image.original_filename, "test_image.jpg")
        self.assertEqual(image.owner, self.user)

        self.assertEqual(response.json(), {"url": image.url})

    @temp_media_root()
    def test_upload_same_file_twice(self):
        old_file = SimpleUploadedFile(
            "old_image.jpg", content=b"file content", content_type="image/jpeg"
        )
        new_file = SimpleUploadedFile(
            "new_image.jpg", content=b"file content", content_type="image/jpeg"
        )
        old_image = Image.objects.create(file=old_file)

        response = self.client.post(self.url, {"upload": new_file})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Image.objects.count(), 1)
        self.assertEqual(response.json(), {"url": old_image.url})
