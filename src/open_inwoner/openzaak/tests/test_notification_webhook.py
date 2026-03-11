import json
import logging  # noqa: TID251 - only used for log levels
from unittest.mock import patch
from urllib.parse import urlencode

from django.test import TestCase, override_settings
from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase
from zds_client import ClientAuth

from notifications.constants import ProcessingStatus
from notifications.models import NotificationRecord
from open_inwoner.openzaak.api.views import ZakenNotificationsWebhookView
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


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
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


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
@patch("open_inwoner.openzaak.tasks.handle_zaken_notification", autospec=True)
class NotificationWebhookAPITestCase(AssertTimelineLogMixin, APITestCase):
    """
    NOTE these tests run against the mounted zaken webhook (eg: ZakenNotificationsWebhookView),
        even though here we only test NotificationsWebhookBaseView functionality
    """

    url = reverse_lazy("openzaak_api:notifications_webhook_zaken")

    def setUp(self):
        super().setUp()
        # Ensure SiteConfiguration exists with notifications enabled
        from open_inwoner.configurations.models import SiteConfiguration

        self.config = SiteConfiguration.get_solo()
        self.config.notifications_cases_enabled = True
        self.config.save()

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

    def test_api_calls_handler_returns_http_204_when_test_notification_received(
        self, mock_handle
    ):
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}
        raw_notification = self.get_raw_notification()

        # set 'test' kanaal
        raw_notification["kanaal"] = "test"

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "received notification on 'test' channel", level=logging.INFO
        )

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

    def test_query_string_effects(self, mock_handle):
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}
        raw_notification = self.get_raw_notification()
        raw_notification["kenmerken"] = {
            "bronorganisatie": "100000009",
            "zaaktype": f"{CATALOGI_ROOT}/zaaktypes/uuid-0002",
            "vertrouwelijkheidaanduiding": "openbaar",
        }

        response = self.client.post(
            self.url + "?" + urlencode({"url": "https://some.url.com"}),
            raw_notification,
            **headers,
            format="json",
            enforce_csrf_checks=True,
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        mock_handle.assert_called_once()
        notification = mock_handle.call_args.args[0]

        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.hoofd_object, raw_notification["hoofdObject"])

    def test_api_marks_record_failed_when_task_scheduling_fails(self, mock_handle):
        """Broker unavailability must leave the record FAILED, not stuck in PENDING."""
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}
        raw_notification = self.get_raw_notification()

        with patch(
            "open_inwoner.openzaak.api.views.process_zaken_notification"
        ) as mock_task:
            mock_task.delay.side_effect = Exception("broker unavailable")
            response = self.client.post(
                self.url, raw_notification, **headers, format="json"
            )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mock_handle.assert_not_called()

        record = NotificationRecord.objects.get()
        self.assertEqual(record.status, ProcessingStatus.FAILED)
        self.assertEqual(record.processing_error, "broker unavailable")

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

    def test_api_returns_http_401_without_valid_auth(self, mock_handle):
        raw_notification = self.get_raw_notification()

        response = self.client.post(self.url, raw_notification, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_handle.assert_not_called()

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
        self.assertEqual(
            response.json(),
            {"resource": ["Dit veld is vereist."]},
        )
        mock_handle.assert_not_called()

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

    def test_api_returns_http_400_on_invalid_json(self, mock_handle):
        """Test that invalid JSON in request body is rejected by DRF"""
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}

        # Send invalid JSON (note: we need to bypass DRF's JSON parser)
        response = self.client.post(
            self.url,
            data="invalid json{",  # Invalid JSON string
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not valid json", response.content.decode())
        mock_handle.assert_not_called()

        # Verify no NotificationRecord was created
        self.assertEqual(NotificationRecord.objects.count(), 0)

    def test_api_accepts_valid_json_only(self, mock_handle):
        """Test that only valid JSON payloads are accepted and stored"""
        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}

        raw_notification = self.get_raw_notification()

        response = self.client.post(
            self.url, raw_notification, **headers, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify NotificationRecord was created with JSON payload
        self.assertEqual(NotificationRecord.objects.count(), 1)
        record = NotificationRecord.objects.first()
        self.assertIsInstance(record.payload, dict)
        self.assertEqual(record.payload["kanaal"], "zaken")
        self.assertEqual(record.payload["resource"], "zaak")

    def test_api_rejects_payload_too_large(self, mock_handle):
        """Test that payloads exceeding max_payload_size are rejected"""
        from notifications.models import NotificationProcessingConfig

        # Set a 1KB limit for testing
        config = NotificationProcessingConfig.get_solo()
        config.max_payload_size = 1024
        config.save()

        SubscriptionFactory.create(client_id="foo", secret="password")
        headers = {"HTTP_AUTHORIZATION": generate_auth_header_value("foo", "password")}

        # Create a large payload that exceeds the limit (1KB + 500 bytes)
        large_payload = {
            "kanaal": "zaken",
            "resource": "zaak",
            "resourceUrl": "http://example.com/zaak/1",
            "data": "x" * 1500,
        }

        response = self.client.post(
            self.url,
            data=large_payload,
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        self.assertIn("payload too large", response.json()["detail"])
        mock_handle.assert_not_called()

        # Verify no NotificationRecord was created
        self.assertEqual(NotificationRecord.objects.count(), 0)

    def test_api_rejects_payload_too_large_without_content_length_header(
        self, mock_handle
    ):
        """Chunked/headerless requests are measured by buffering when Content-Length is absent"""
        from notifications.models import NotificationProcessingConfig

        config = NotificationProcessingConfig.get_solo()
        config.max_payload_size = 1024
        config.save()

        SubscriptionFactory.create(client_id="foo", secret="password")

        large_payload = {
            "kanaal": "zaken",
            "resource": "zaak",
            "resourceUrl": "http://example.com/zaak/1",
            "data": "x" * 1500,
        }

        factory = APIRequestFactory()
        request = factory.post(
            self.url,
            data=json.dumps(large_payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=generate_auth_header_value("foo", "password"),
        )
        del request.META["CONTENT_LENGTH"]

        response = ZakenNotificationsWebhookView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        self.assertIn("payload too large", response.data["detail"])
        mock_handle.assert_not_called()
        self.assertEqual(NotificationRecord.objects.count(), 0)
