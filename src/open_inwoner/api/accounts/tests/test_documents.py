from django.urls import reverse

from django_webtest import WebTest
from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from webtest.forms import Upload

from open_inwoner.accounts.models import Document
from open_inwoner.accounts.tests.factories import (
    DocumentFactory,
    TokenFactory,
    UserFactory,
)


@temp_private_root()
class TestListDocuments(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.document = DocumentFactory(owner=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_documents_endpoint_returns_the_documents_of_the_authorized_user(self):
        response = self.app.get(reverse("api:documents-list"), headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            [
                {
                    "uuid": str(self.document.uuid),
                    "url": f"http://testserver/api/documents/{str(self.document.uuid)}/",
                    "name": self.document.name,
                    "file": f"http://testserver/private_files/{self.document.file.name}",
                    "createdOn": "2021-10-18T15:00:00+02:00",
                    "updatedOn": "2021-10-18T15:00:00+02:00",
                },
            ],
        )

    def test_documents_endpoint_fails_when_user_is_unauthorized(self):
        response = self.app.get(reverse("api:documents-list"), status=401)
        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_documents_endpoint_fails_to_return_documents_owned_by_another_user(self):
        user = UserFactory()
        document = DocumentFactory(owner=user)
        url = reverse("api:documents-detail", kwargs={"uuid": document.uuid})
        response = self.app.get(url, headers=self.headers, status=404)

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


@temp_private_root()
class TestCreateDocument(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_documents_endpoint_saves_document_of_the_authorized_user(self):
        response = self.app.post(
            reverse("api:documents-list"),
            {
                "name": "Document name",
                "file": Upload("filename.txt", b"contents"),
            },
            headers=self.headers,
        )
        db_documents = Document.objects.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_documents.count(), 1)
        self.assertEqual(db_documents[0].owner.id, self.user.id)

    def test_documents_endpoint_fails_to_create_new_document_when_user_is_unauthorized(
        self,
    ):
        response = self.app.post(
            reverse("api:documents-list"),
            {
                "name": "Document name",
                "file": Upload("filename.txt", b"contents"),
            },
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_documents_endpoint_fails_to_create_new_document_without_sending_a_file(
        self,
    ):
        response = self.app.post(
            reverse("api:documents-list"),
            {},
            headers=self.headers,
            status=400,
        )
        db_documents = Document.objects.all()

        self.assertEqual(db_documents.count(), 0)
        self.assertEqual(response.json, {"file": ["Er is geen bestand opgestuurd."]})


@temp_private_root()
class TestUpdateDocument(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.document = DocumentFactory(owner=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    @freeze_time("2021-10-18 13:00:00")
    def test_documents_endpoint_updates_document_of_authorized_user(self):
        url = reverse("api:documents-detail", kwargs={"uuid": self.document.uuid})
        response = self.app.put(
            url,
            {
                "name": "Updated document name",
                "file": Upload("new_filename.txt", b"contents"),
            },
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.document.uuid),
                "name": "Updated document name",
                "file": f"http://testserver/private_files/new_filename.txt",
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/documents/{str(self.document.uuid)}/",
            },
        )

    def test_documents_endpoint_fails_to_update_document_when_user_is_unauthorized(
        self,
    ):
        url = reverse("api:documents-detail", kwargs={"uuid": self.document.uuid})
        response = self.app.put(
            url,
            {
                "name": "Updated document name",
                "file": Upload("new_filename.txt", b"contents"),
            },
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_documents_endpoint_fails_to_update_document_owned_by_another_user(self):
        user = UserFactory()
        document = DocumentFactory(owner=user)
        url = reverse("api:documents-detail", kwargs={"uuid": document.uuid})
        response = self.app.put(
            url,
            {
                "name": "Updated document name",
                "file": Upload("new_filename.txt", b"contents"),
            },
            headers=self.headers,
            status=404,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


@temp_private_root()
class TestPartialUpdateDocument(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.document = DocumentFactory(owner=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    @freeze_time("2021-10-18 13:00:00")
    def test_documents_endpoint_updates_file(self):
        url = reverse("api:documents-detail", kwargs={"uuid": self.document.uuid})
        response = self.app.patch(
            url,
            {
                "file": Upload("new_filename.txt", b"contents"),
            },
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.document.uuid),
                "name": self.document.name,
                "file": f"http://testserver/private_files/new_filename.txt",
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/documents/{str(self.document.uuid)}/",
            },
        )

    def test_documents_endpoint_fails_to_update_name_when_user_is_unauthorized(
        self,
    ):
        url = reverse("api:documents-detail", kwargs={"uuid": self.document.uuid})
        response = self.app.patch_json(
            url,
            {"name": "Updated name"},
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_documents_endpoint_fails_to_update_name_of_a_document_owned_by_another_user(
        self,
    ):
        user = UserFactory()
        document = DocumentFactory(owner=user)
        url = reverse("api:documents-detail", kwargs={"uuid": document.uuid})
        response = self.app.patch_json(
            url,
            {"name": "Updated name"},
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


@temp_private_root()
class TestDeleteDocument(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.document = DocumentFactory(owner=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_documents_endpoint_deletes_document_when_is_authorized(self):
        url = reverse("api:documents-detail", kwargs={"uuid": self.document.uuid})
        response = self.app.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_documents_endpoint_fails_to_delete_document_when_user_is_unauthorized(
        self,
    ):
        url = reverse("api:documents-detail", kwargs={"uuid": self.document.uuid})
        response = self.app.delete(url, status=401)

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_documents_endpoint_fails_to_delete_document_owned_by_another_user(self):
        user = UserFactory()
        document = DocumentFactory(owner=user)
        url = reverse("api:documents-detail", kwargs={"uuid": document.uuid})
        response = self.app.delete(
            url,
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})
