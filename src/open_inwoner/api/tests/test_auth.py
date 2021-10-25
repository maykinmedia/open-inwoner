from django.urls import reverse

from django_webtest import WebTest
from rest_framework import status

from ...accounts.tests.factories import UserFactory
from .factories import TokenFactory


class TestTokenAuthentication(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.user_token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {str(self.user_token.key)}"}

    def test_authenticated_user_receives_token(self):
        user_credentials = {"email": self.user.email, "password": "secret"}
        response = self.app.post_json(reverse("api:rest_login"), user_credentials)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json, {"key": str(self.user_token.key)})

    def test_wrong_credentials_in_the_body_returns_status_400(self):
        user_credentials = {"email": "", "password": "wrong"}
        response = self.app.post_json(
            reverse("api:rest_login"), user_credentials, status=400
        )

        self.assertEqual(
            response.json,
            {"nonFieldErrors": ["Kan niet inloggen met de opgegeven inloggegevens."]},
        )

    def test_valid_token_returns_status_200(self):
        user_credentials = {"email": self.user.email, "password": "secret"}
        response = self.app.get(
            reverse("api:rest_user_details"), user_credentials, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_returns_status_401(self):
        headers = {"AUTHORIZATION": "Token invalid-token"}
        response = self.app.get(
            reverse("api:rest_user_details"), headers=headers, status=401
        )

        self.assertEqual(response.json, {"detail": "Ongeldige token."})
