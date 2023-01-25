import logging
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase
from zds_client import ClientAuth

from open_inwoner.openzaak.api_models import Notification
from open_inwoner.openzaak.auth import get_valid_subscriptions_from_bearer
from open_inwoner.openzaak.exceptions import (
    InvalidAuth,
    InvalidAuthForClientID,
    NoSubscriptionForClientID,
)
from open_inwoner.openzaak.tests.factories import SubscriptionFactory
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin

from .shared import CATALOGI_ROOT, ZAKEN_ROOT


def generate_auth(client_id, secret):
    # this emulates the token creation from Subscription.register()
    client_auth = ClientAuth(
        # note we only add the fields we're interested in
        client_id=client_id,
        secret=secret,
    )
    return client_auth


def generate_auth_header_value(client_id, secret):
    # this emulates the token creation from Subscription.register()
    client_auth = generate_auth(client_id, secret)
    auth_value = client_auth.credentials()["Authorization"]
    return auth_value


class NotificationSubscriptionAuthTest(TestCase):
    def test_valid_auth_retrieves_subscription(self):
        subscription = SubscriptionFactory(client_id="foo", secret="password")

        SubscriptionFactory(client_id="foo", secret="not_password")
        SubscriptionFactory(client_id="not_foo", secret="not_password")
        SubscriptionFactory(client_id="not_foo", secret="password")

        auth_value = generate_auth_header_value("foo", "password")

        actual = get_valid_subscriptions_from_bearer(auth_value)
        self.assertEqual(actual, subscription)

    def test_unknown_client_id_raises_exception(self):
        SubscriptionFactory(client_id="foo", secret="password")

        auth_value = generate_auth_header_value("bar", "not_password")

        with self.assertRaises(NoSubscriptionForClientID):
            get_valid_subscriptions_from_bearer(auth_value)

    def test_known_client_id_with_bad_secret_raises_exception(self):
        SubscriptionFactory(client_id="foo", secret="password")

        auth_value = generate_auth_header_value("foo", "not_password")

        with self.assertRaises(InvalidAuthForClientID):
            get_valid_subscriptions_from_bearer(auth_value)

    def test_invalid_auth_header_raises_exception(self):
        SubscriptionFactory(client_id="foo", secret="password")

        auth_value = "not a valid bearer token"

        with self.assertRaises(InvalidAuth):
            get_valid_subscriptions_from_bearer(auth_value)


@patch("open_inwoner.openzaak.api.views.handle_zaken_notification")
class NotificationWebhookAPITestCase(AssertTimelineLogMixin, APITestCase):
    """
    NOTE these tests run against the mounted zaken webhook (eg: ZakenNotificationsWebhookView),
        even though here we only test NotificationsWebhookBaseView functionality
    """

    url = reverse_lazy("openzaak_api:notifications_webhook_zaken")

    def get_raw_notification(
        self,
    ):
        raw_notification = {
            "kanaal": "zaken",
            "hoofdObject": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            "resource": "zaak",
            "resourceUrl": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            "actie": "partial_update",
            "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
            "kenmerken": {},
        }
        return raw_notification

    def test_api_calls_handler_returns_http_204_when_valid(self, mock_handle):
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}
        raw_notification = self.get_raw_notification()
        raw_notification["kenmerken"] = {
            "bronorganisatie": "100000009",
            "zaaktype": f"{CATALOGI_ROOT}/zaaktypes/uuid-0002",
            "vertrouwelijkheidaanduiding": "openbaar",
        }

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        mock_handle.assert_called_once()
        notification = mock_handle.call_args.args[0]

        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.hoofd_object, raw_notification["hoofdObject"])

        self.assertTimelineLog("handled notification", level=logging.DEBUG)

    def test_api_returns_http_500_when_valid_but_handler_raises(self, mock_handle):
        mock_handle.side_effect = Exception("whoopsie")

        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}
        raw_notification = self.get_raw_notification()

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        mock_handle.assert_called_once()
        notification = mock_handle.call_args.args[0]

        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.hoofd_object, raw_notification["hoofdObject"])

        self.assertTimelineLog(
            "error handling notification: whoopsie", level=logging.ERROR
        )

    def test_api_returns_http_401_without_valid_auth(self, mock_handle):
        raw_notification = self.get_raw_notification()

        response = self.client.post(self.url, raw_notification, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_handle.assert_not_called()

        self.assertTimelineLog("missing Authorization header", level=logging.ERROR)

    def test_api_returns_http_401_without_matching_subscription(self, mock_handle):
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {
            "HTTP_AUTHORIZATION": generate_auth_header_value("not_foo", "password")
        }
        raw_notification = self.get_raw_notification()

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_handle.assert_not_called()

        self.assertTimelineLog(
            "no subscriptions for client_id 'not_foo'", level=logging.ERROR
        )

    def test_api_returns_http_401_on_missing_notification_members(self, mock_handle):
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}

        raw_notification = self.get_raw_notification()
        # missing field resource
        del raw_notification["resource"]

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"resource": ["Dit veld is vereist."]})
        mock_handle.assert_not_called()

        self.assertTimelineLog("cannot deserialize notification", level=logging.ERROR)

    def test_api_returns_http_401_on_invalid_subscription_kanaal(self, mock_handle):
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}
        raw_notification = self.get_raw_notification()

        # bad kanaal
        raw_notification["kanaal"] = "not_subscribed_kanaal"

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "detail": "notification channel 'not_subscribed_kanaal' not subscribed to"
            },
        )
        mock_handle.assert_not_called()

        self.assertTimelineLog(
            "notification channel 'not_subscribed_kanaal' not subscribed to",
            level=logging.ERROR,
        )

    def test_api_returns_http_401_on_invalid_webhook_kanaal(self, mock_handle):
        SubscriptionFactory.create(
            client_id="foo", secret="password", channels=["not_webhook_kanaal"]
        )
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}
        raw_notification = self.get_raw_notification()

        # bad kanaal
        raw_notification["kanaal"] = "not_webhook_kanaal"

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "detail": "notification channel 'not_webhook_kanaal' not acceptable by webhook"
            },
        )
        mock_handle.assert_not_called()

        self.assertTimelineLog(
            "notification channel 'not_webhook_kanaal' not acceptable by webhook",
            level=logging.ERROR,
        )
