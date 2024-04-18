from unittest.mock import patch
from urllib.parse import parse_qs

from django.test import RequestFactory, TestCase
from django.utils.translation import gettext as _

import requests_mock

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.utils.test import ClearCachesMixin

from ..forms import NewsletterSubscriptionForm
from ..models import LapostaConfig
from .factories import LapostaListFactory, MemberFactory

LAPOSTA_API_ROOT = "https://laposta.local/api/v2/"


@requests_mock.Mocker()
class NewsletterSubscriptionFormTestCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory()
        self.user.verified_email = self.user.email
        self.user.save()
        self.assertTrue(self.user.has_verified_email())

        self.request = RequestFactory().get("/")
        self.request.user = self.user

        self.config = LapostaConfig.get_solo()
        self.config.api_root = LAPOSTA_API_ROOT
        self.config.basic_auth_username = "username"
        self.config.basic_auth_password = "password"
        self.config.limit_list_selection_to = ["123", "456", "789"]
        self.config.save()

        self.list1 = LapostaListFactory.build(
            list_id="123", name="Nieuwsbrief1", remarks="foo"
        )
        self.list2 = LapostaListFactory.build(
            list_id="456", name="Nieuwsbrief2", remarks="bar"
        )
        self.list3 = LapostaListFactory.build(
            list_id="789", name="Nieuwsbrief3", remarks="baz"
        )

    def setUpMocks(self, m):
        m.get(
            f"{LAPOSTA_API_ROOT}list",
            json={
                "data": [
                    {"list": self.list1.model_dump()},
                    {"list": self.list2.model_dump()},
                    {"list": self.list3.model_dump()},
                ]
            },
        )

    def test_save_form(self, m):
        """
        Verify that the form can create and delete subscriptions
        """
        self.setUpMocks(m)

        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=123",
            json={
                "member": MemberFactory.build(
                    list_id="123",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=456",
            json={
                "member": MemberFactory.build(
                    list_id="456",
                    member_id="8765433",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=789", status_code=400
        )

        form = NewsletterSubscriptionForm(data={}, user=self.user)

        # User already has a subscription for the first two newsletters
        self.assertEqual(form["newsletters"].initial, ["123", "456"])

        form = NewsletterSubscriptionForm(
            data={"newsletters": ["456", "789"]}, user=self.user
        )

        self.assertTrue(form.is_valid())

        post_matcher = m.post(
            f"{LAPOSTA_API_ROOT}member",
            json={
                "member": MemberFactory.build(
                    list_id="789",
                    member_id="member789",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        delete_matcher = m.delete(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=123"
        )

        form.save(self.request)

        self.assertEqual(
            len(post_matcher.request_history),
            1,
            "Subscribe to list if present in the form data (and no subscription exists yet)",
        )

        [post_request] = post_matcher.request_history

        self.assertEqual(
            parse_qs(post_request.body),
            {"list_id": ["789"], "ip": ["127.0.0.1"], "email": [self.user.email]},
        )

        # Because list_id 123 was present in the
        self.assertEqual(
            len(delete_matcher.request_history),
            1,
            "Unsubscribe from list if not present in the form data",
        )

    def test_save_form_create_duplicate_subscription(self, m):
        """
        Verify that the client properly handles the scenario where the user is a member
        of the list in the API, but the user tries to create a new subscription for it
        """
        self.setUpMocks(m)

        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=123", status_code=400
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=456", status_code=400
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=789", status_code=400
        )

        form = NewsletterSubscriptionForm(data={"newsletters": ["789"]}, user=self.user)

        self.assertTrue(form.is_valid())

        # The subscription could have been created somewhere else in the meantime
        post_matcher = m.post(
            f"{LAPOSTA_API_ROOT}member",
            json={
                "error": {
                    "type": "invalid_input",
                    "message": "Email address exists",
                    "code": 204,
                    "parameter": "email",
                    "id": "pqfozv6xqu",
                    "member_id": "member789",
                }
            },
            status_code=400,
        )

        form.save(self.request)

        self.assertEqual(len(post_matcher.request_history), 1)

    def test_save_form_delete_non_existent_subscription(self, m):
        """
        Verify that the client properly handles the scenario where the user tries to
        delete a subscription that does not exist in the API
        """
        self.setUpMocks(m)

        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=123", status_code=400
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=456", status_code=400
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=789",
            json={
                "member": MemberFactory.build(
                    list_id="789",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )

        form = NewsletterSubscriptionForm(data={"newsletters": []}, user=self.user)

        self.assertTrue(form.is_valid())

        delete_matcher = m.delete(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=789",
            json={
                "error": {
                    "type": "invalid_input",
                    "message": "Unknown member",
                    "code": 203,
                    "parameter": "member_id",
                }
            },
            status_code=400,
        )

        form.save(self.request)

        self.assertEqual(len(delete_matcher.request_history), 1)

    def test_save_form_raises_errors(self, m):
        """
        Form should return errors if unexpected errors occur when performing API calls
        """
        self.setUpMocks(m)

        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=123", status_code=400
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=456",
            json={
                "member": MemberFactory.build(
                    list_id="456",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=789", status_code=400
        )

        form = NewsletterSubscriptionForm(data={"newsletters": ["789"]}, user=self.user)

        self.assertTrue(form.is_valid())

        post_matcher = m.post(
            f"{LAPOSTA_API_ROOT}member",
            json={
                "error": {
                    "type": "internal",
                    "message": "Internal server error",
                }
            },
            status_code=500,
        )
        delete_matcher = m.delete(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=456",
            json={
                "error": {
                    "type": "internal",
                    "message": "Internal server error",
                }
            },
            status_code=500,
        )

        form.save(self.request)

        self.assertEqual(len(post_matcher.request_history), 1)
        self.assertEqual(len(delete_matcher.request_history), 1)
        self.assertEqual(
            form.errors,
            {
                "newsletters": [
                    _(
                        "Something went wrong while trying to subscribe to "
                        "'{list_name}', please try again later"
                    ).format(list_name="Nieuwsbrief3"),
                    _(
                        "Something went wrong while trying to unsubscribe from "
                        "'{list_name}', please try again later"
                    ).format(list_name="Nieuwsbrief2"),
                ]
            },
        )

    @patch("open_inwoner.laposta.forms.create_laposta_client")
    def test_form__disables_when_email_not_verified(self, m, mock_create_client):
        """
        Verify that form actions cannot be performed if the user's email is not verified
        """
        self.setUpMocks(m)

        self.user.verified_email = ""
        self.user.save()
        self.assertFalse(self.user.has_verified_email())

        m.get(
            f"{LAPOSTA_API_ROOT}member/{self.user.email}?list_id=123",
            json={
                "member": MemberFactory.build(
                    list_id="123",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )

        form = NewsletterSubscriptionForm(data={}, user=self.user)

        # We don't get any newletters if not using verified email
        self.assertEqual(form["newsletters"].initial, None)

        # Because client was never built (and no request-mock exception was thrown)
        mock_create_client.assert_not_called()

        # Check forced save() doesn't do anything
        form = NewsletterSubscriptionForm(data={"newsletters": ["123"]}, user=self.user)
        form.save(self.request)

        # Client was never built (and no request-mock exception was thrown)
        mock_create_client.assert_not_called()
