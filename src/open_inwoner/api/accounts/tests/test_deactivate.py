from datetime import date

from django.urls import reverse

from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import TokenFactory, UserFactory


class TestPartialUpdateDeactivate(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.token = TokenFactory(created_for=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    @freeze_time("2021-10-01")
    def test_endpoint_updates_user(self):
        url = reverse("api:deactivate_user")
        response = self.client.patch(url)
        user = User.objects.get(id=self.user.id)

        self.assertEqual(user.deactivated_on, date(2021, 10, 1))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"detail": "User has been deactivated."})

    @freeze_time("2021-10-01")
    def test_endpoint_fails_with_unauthenticated_user(self):
        # stop including credentials
        self.client.credentials()

        url = reverse("api:deactivate_user")
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(), {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    @freeze_time("2021-10-01")
    def test_endpoint_does_not_update_staff_user(self):
        user = UserFactory(is_staff=True)
        user_token = TokenFactory(created_for=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {user_token.key}")
        url = reverse("api:deactivate_user")
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json(), {"detail": "Staff user cannot be deactivated."}
        )

    @freeze_time("2021-10-01")
    def test_endpoint_does_not_allow_PUT_method(self):
        url = reverse("api:deactivate_user")
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.json(), {"detail": 'Methode "PUT" not allowed.'})
