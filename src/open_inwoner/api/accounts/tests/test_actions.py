from django.urls import reverse

from django_webtest import WebTest
from freezegun import freeze_time
from rest_framework import status

from open_inwoner.accounts.models import Action
from open_inwoner.accounts.tests.factories import (
    ActionFactory,
    TokenFactory,
    UserFactory,
)


class TestListActions(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.action = ActionFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_actions_endpoint_returns_the_actions_of_the_authorized_user(self):
        response = self.app.get(reverse("api:actions-list"), headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            [
                {
                    "uuid": str(self.action.uuid),
                    "name": self.action.name,
                    "createdOn": "2021-10-18T15:00:00+02:00",
                    "updatedOn": "2021-10-18T15:00:00+02:00",
                    "url": f"http://testserver/api/actions/{str(self.action.uuid)}/",
                },
            ],
        )

    def test_actions_endpoint_fails_when_user_is_unauthorized(self):
        response = self.app.get(reverse("api:actions-list"), status=401)
        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_actions_endpoint_fails_to_return_actions_of_another_user(self):
        user = UserFactory()
        action = ActionFactory(created_by=user)
        url = reverse("api:actions-detail", kwargs={"uuid": action.uuid})
        response = self.app.get(url, headers=self.headers, status=404)

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestCreateAction(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.action = ActionFactory.build(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_actions_endpoint_saves_action_of_the_authorized_user(self):
        response = self.app.post_json(
            reverse("api:actions-list"),
            {
                "name": self.action.name,
            },
            headers=self.headers,
        )
        db_actions = Action.objects.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_actions.count(), 1)
        self.assertEqual(db_actions[0].created_by.id, self.user.id)

    def test_actions_endpoint_fails_to_create_new_action_when_user_is_unauthorized(
        self,
    ):
        response = self.app.post_json(
            reverse("api:actions-list"),
            {
                "name": self.action.name,
            },
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )


class TestUpdateAction(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.action = ActionFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    @freeze_time("2021-10-18 13:00:00")
    def test_actions_endpoint_updates_action_of_authorized_user(self):
        url = reverse("api:actions-detail", kwargs={"uuid": self.action.uuid})
        response = self.app.put_json(
            url,
            {"name": "Updated name"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.action.uuid),
                "name": "Updated name",
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/actions/{str(self.action.uuid)}/",
            },
        )

    def test_actions_endpoint_fails_to_update_action_when_user_is_unauthorized(self):
        url = reverse("api:actions-detail", kwargs={"uuid": self.action.uuid})
        response = self.app.put_json(
            url,
            {"name": "Updated name"},
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_actions_endpoint_fails_to_update_action_created_by_another_user(self):
        user = UserFactory()
        action = ActionFactory(created_by=user)
        url = reverse("api:actions-detail", kwargs={"uuid": action.uuid})
        response = self.app.put_json(
            url,
            {"name": "Updated name"},
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestPartialUpdateAction(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.action = ActionFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    @freeze_time("2021-10-18 13:00:00")
    def test_actions_endpoint_updates_name(self):
        url = reverse("api:actions-detail", kwargs={"uuid": self.action.uuid})
        response = self.app.patch_json(
            url,
            {"name": "Updated name"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.action.uuid),
                "name": "Updated name",
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/actions/{str(self.action.uuid)}/",
            },
        )

    def test_actions_endpoint_fails_to_update_name_when_user_is_unauthorized(
        self,
    ):
        url = reverse("api:actions-detail", kwargs={"uuid": self.action.uuid})
        response = self.app.patch_json(
            url,
            {"name": "Updated name"},
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_actions_endpoint_fails_to_update_name_of_an_action_created_by_another_user(
        self,
    ):
        user = UserFactory()
        action = ActionFactory(created_by=user)
        url = reverse("api:actions-detail", kwargs={"uuid": action.uuid})
        response = self.app.patch_json(
            url,
            {"name": "Updated name"},
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestDeleteAction(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.action = ActionFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_actions_endpoint_deletes_action_when_user_is_authorized(self):
        url = reverse("api:actions-detail", kwargs={"uuid": self.action.uuid})
        response = self.app.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_actions_endpoint_fails_to_delete_action_when_user_is_unauthorized(self):
        url = reverse("api:actions-detail", kwargs={"uuid": self.action.uuid})
        response = self.app.delete(url, status=401)

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_actions_endpoint_fails_to_delete_action_created_by_another_user(self):
        user = UserFactory()
        action = ActionFactory(created_by=user)
        url = reverse("api:actions-detail", kwargs={"uuid": action.uuid})
        response = self.app.delete(
            url,
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})
