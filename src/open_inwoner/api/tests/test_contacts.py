from django.urls import reverse

from django_webtest import WebTest
from freezegun import freeze_time
from rest_framework import status

from ...accounts.models import Contact
from ...accounts.tests.factories import UserFactory
from .factories import ContactFactory


class TestListContacts(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.contact1 = ContactFactory(created_by=self.user1)
        self.contact2 = ContactFactory(created_by=self.user2)

    def test_contacts_endpoint_returns_the_contacts_of_the_authorized_user(self):
        response = self.app.get(reverse("api:contacts-list"), user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            [
                {
                    "uuid": str(self.contact1.uuid),
                    "firstName": self.contact1.first_name,
                    "lastName": self.contact1.last_name,
                    "email": None,
                    "phonenumber": "",
                    "createdOn": "2021-10-18T15:00:00+02:00",
                    "updatedOn": "2021-10-18T15:00:00+02:00",
                    "url": f"http://testserver/api/contacts/{str(self.contact1.uuid)}/",
                },
            ],
        )

    def test_contacts_endpoint_fails_when__user_is_unauthorized(self):
        response = self.app.get(reverse("api:contacts-list"), status=401)
        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_contacts_endpoint_fails_to_return_contacts_of_another_user(self):
        url = reverse("api:contacts-detail", kwargs={"uuid": self.contact2.uuid})
        response = self.app.get(url, user=self.user1, status=404)

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestCreateContact(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()
        self.contact = ContactFactory.build(created_by=self.user)

    def test_contacts_endpoint_saves_contact_of_the_authorized_user(self):
        response = self.app.post_json(
            reverse("api:contacts-list"),
            {
                "first_name": self.contact.first_name,
                "last_name": self.contact.last_name,
            },
            user=self.user,
        )
        db_contacts = Contact.objects.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_contacts.count(), 1)
        self.assertEqual(db_contacts[0].created_by.id, self.user.id)

    def test_contacts_endpoint_fails_to_create_new_contact_when_user_is_unauthorized(
        self,
    ):
        response = self.app.post_json(
            reverse("api:contacts-list"),
            {
                "first_name": self.contact.first_name,
                "last_name": self.contact.last_name,
            },
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_contacts_endpoint_fails_to_create_new_contact_without_first_or_last_name(
        self,
    ):
        response = self.app.post_json(
            reverse("api:contacts-list"),
            {},
            user=self.user,
            status=400,
        )
        db_contacts = Contact.objects.all()

        self.assertEqual(db_contacts.count(), 0)
        self.assertEqual(
            response.json,
            {
                "firstName": ["Dit veld is vereist."],
                "lastName": ["Dit veld is vereist."],
            },
        )


class TestUpdateContact(WebTest):
    csrf_checks = False

    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user1 = UserFactory()
        self.contact1 = ContactFactory(created_by=self.user1)

    @freeze_time("2021-10-18 13:00:00")
    def test_contacts_endpoint_updates_contact_of_authorized_user(self):
        url = reverse("api:contacts-detail", kwargs={"uuid": self.contact1.uuid})
        response = self.app.put_json(
            url,
            {"first_name": "Updated first name", "last_name": "Updated last name"},
            user=self.user1,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.contact1.uuid),
                "firstName": "Updated first name",
                "lastName": "Updated last name",
                "email": None,
                "phonenumber": "",
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/contacts/{str(self.contact1.uuid)}/",
            },
        )

    def test_contacts_endpoint_fails_to_update_contact_when_user_is_unauthorized(self):
        url = reverse("api:contacts-detail", kwargs={"uuid": self.contact1.uuid})
        response = self.app.put_json(
            url,
            {"first_name": "Updated first name", "last_name": "Updated last name"},
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_contacts_endpoint_fails_to_update_contact_created_by_another_user(self):
        user2 = UserFactory()
        contact2 = ContactFactory(created_by=user2)
        url = reverse("api:contacts-detail", kwargs={"uuid": contact2.uuid})
        response = self.app.put_json(
            url,
            {"first_name": "Updated first name", "last_name": "Updated last name"},
            status=404,
            user=self.user1,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestPartialUpdateContact(WebTest):
    csrf_checks = False

    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user1 = UserFactory()
        self.contact1 = ContactFactory(created_by=self.user1)

    @freeze_time("2021-10-18 13:00:00")
    def test_contacts_endpoint_updates_first_name(self):
        url = reverse("api:contacts-detail", kwargs={"uuid": self.contact1.uuid})
        response = self.app.patch_json(
            url,
            {"first_name": "Updated first name"},
            user=self.user1,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.contact1.uuid),
                "firstName": "Updated first name",
                "lastName": self.contact1.last_name,
                "email": None,
                "phonenumber": "",
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/contacts/{str(self.contact1.uuid)}/",
            },
        )

    def test_contacts_endpoint_fails_to_update_first_name_when_user_is_unauthorized(
        self,
    ):
        url = reverse("api:contacts-detail", kwargs={"uuid": self.contact1.uuid})
        response = self.app.patch_json(
            url,
            {"first_name": "Updated first name"},
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_contacts_endpoint_fails_to_update_first_name_of_a_contact_created_by_another_user(
        self,
    ):
        user2 = UserFactory()
        contact2 = ContactFactory(created_by=user2)
        url = reverse("api:contacts-detail", kwargs={"uuid": contact2.uuid})
        response = self.app.patch_json(
            url,
            {"first_name": "Updated first name"},
            status=404,
            user=self.user1,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestDeleteContact(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user1 = UserFactory()
        self.contact1 = ContactFactory(created_by=self.user1)

    def test_contacts_endpoint_deletes_contact_when_user_is_authorized(self):
        url = reverse("api:contacts-detail", kwargs={"uuid": self.contact1.uuid})
        response = self.app.delete(url, user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_contacts_endpoint_fails_to_delete_contact_when_user_is_unauthorized(self):
        url = reverse("api:contacts-detail", kwargs={"uuid": self.contact1.uuid})
        response = self.app.delete(url, status=401)

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_contacts_endpoint_fails_to_delete_contact_created_by_another_user(self):
        user2 = UserFactory()
        user2_contact = ContactFactory(created_by=user2)
        url = reverse("api:contacts-detail", kwargs={"uuid": user2_contact.uuid})
        response = self.app.delete(
            url,
            status=404,
            user=self.user1,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})
