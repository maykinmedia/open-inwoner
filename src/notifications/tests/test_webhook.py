from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase

import requests_mock
from requests.exceptions import RequestException
from zgw_consumers.constants import APITypes
from zgw_consumers.models.services import Service

from notifications.admin import deregister_webhook, register_webhook
from notifications.models import NotificationsAPIConfig, Subscription

from .utils import make_request_with_middleware


class NotificationsAPIWebhookTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
            oas="http://some-api-root/api/v1/schema/openapi.yaml",
            secret="test-secret",
        )
        cls.config = NotificationsAPIConfig.objects.create(
            notifications_api_service=service
        )
        cls.config.save()

        service_other = Service.objects.create(
            api_root="http://other-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service-other",
            oas="http://other-api-root/api/v1/schema/openapi.yaml",
            secret="test-secret-other",
        )
        cls.config_other = NotificationsAPIConfig.objects.create(
            notifications_api_service=service_other
        )
        cls.config_other.save()

    @requests_mock.Mocker()
    def test_register_webhook_success(self, m):
        m.post(
            "http://some-api-root/api/v1/abonnement",
            json={
                "url": "https://example.com/api/v1/abonnementen/1",
            },
        )
        m.post(
            "http://other-api-root/api/v1/abonnement",
            json={
                "url": "https://example.com/api/v1/abonnementen/2",
            },
        )

        subscription = Subscription.objects.create(
            notifications_api_config=self.config,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
        )
        subscription_other = Subscription.objects.create(
            notifications_api_config=self.config_other,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
        )

        request_with_middleware = make_request_with_middleware()

        register_webhook(object, request_with_middleware, Subscription.objects.all())

        messages = list(get_messages(request_with_middleware))

        self.assertEqual(len(messages), 0)

        subscription.refresh_from_db()
        self.assertEqual(
            subscription._subscription, "https://example.com/api/v1/abonnementen/1"
        )
        subscription_other.refresh_from_db()
        self.assertEqual(
            subscription_other._subscription,
            "https://example.com/api/v1/abonnementen/2",
        )

    def test_register_webhook_request_exception(self):
        Subscription.objects.create(
            notifications_api_config=self.config,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
        )

        request_with_middleware = make_request_with_middleware()

        with patch(
            "requests.sessions.Session.post", side_effect=RequestException("exception")
        ):
            register_webhook(
                object, request_with_middleware, Subscription.objects.all()
            )

        messages = list(get_messages(request_with_middleware))

        self.assertEqual(len(messages), 1)

    @requests_mock.Mocker()
    def test_deregister_webhook_success(self, m):
        m.delete("http://some-api-root/api/v1/abonnement/1", status_code=204)
        m.delete("http://other-api-root/api/v1/abonnement/2", status_code=204)

        subscription = Subscription.objects.create(
            notifications_api_config=self.config,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
            _subscription="http://some-api-root/api/v1/abonnement/1",
        )
        subscription_other = Subscription.objects.create(
            notifications_api_config=self.config_other,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
            _subscription="http://other-api-root/api/v1/abonnement/2",
        )

        subscription.deregister()
        subscription_other.deregister()

        subscription.refresh_from_db()
        self.assertEqual(subscription._subscription, "")

        # Verify that DELETE requests were made to both subscription URLs
        self.assertEqual(len(m.request_history), 2)
        self.assertEqual(m.request_history[0].method, "DELETE")
        self.assertEqual(
            m.request_history[0].url, "http://some-api-root/api/v1/abonnement/1"
        )
        self.assertEqual(m.request_history[1].method, "DELETE")
        self.assertEqual(
            m.request_history[1].url, "http://other-api-root/api/v1/abonnement/2"
        )

        subscription_other.refresh_from_db()
        self.assertEqual(subscription_other._subscription, "")

    @requests_mock.Mocker()
    def test_deregister_webhook_no_subscription(self, m):
        subscription = Subscription.objects.create(
            notifications_api_config=self.config,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
            _subscription="",
        )

        # Should not raise an exception
        subscription.deregister()

        subscription.refresh_from_db()
        self.assertEqual(subscription._subscription, "")

        # Verify that no HTTP requests were made since there's no subscription to deregister
        self.assertEqual(len(m.request_history), 0)

    @requests_mock.Mocker()
    def test_deregister_webhook_admin_action_success(self, m):
        m.delete("http://some-api-root/api/v1/abonnement/1", status_code=204)
        m.delete("http://other-api-root/api/v1/abonnement/2", status_code=204)

        subscription = Subscription.objects.create(
            notifications_api_config=self.config,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
            _subscription="http://some-api-root/api/v1/abonnement/1",
        )
        subscription_other = Subscription.objects.create(
            notifications_api_config=self.config_other,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
            _subscription="http://other-api-root/api/v1/abonnement/2",
        )

        request_with_middleware = make_request_with_middleware()

        deregister_webhook(object, request_with_middleware, Subscription.objects.all())

        messages = list(get_messages(request_with_middleware))
        self.assertEqual(len(messages), 0)

        subscription.refresh_from_db()
        self.assertEqual(subscription._subscription, "")
        subscription_other.refresh_from_db()
        self.assertEqual(subscription_other._subscription, "")

        # Verify that DELETE requests were made to both subscription URLs
        self.assertEqual(len(m.request_history), 2)
        self.assertEqual(m.request_history[0].method, "DELETE")
        self.assertEqual(
            m.request_history[0].url, "http://some-api-root/api/v1/abonnement/1"
        )
        self.assertEqual(m.request_history[1].method, "DELETE")
        self.assertEqual(
            m.request_history[1].url, "http://other-api-root/api/v1/abonnement/2"
        )

    def test_deregister_webhook_admin_action_request_exception(self):
        subscription = Subscription.objects.create(
            notifications_api_config=self.config,
            callback_url="https://example.com/callback",
            client_id="client_id",
            secret="secret",
            channels=["zaken"],
            _subscription="http://some-api-root/api/v1/abonnement/1",
        )

        request_with_middleware = make_request_with_middleware()

        with patch(
            "requests.sessions.Session.delete",
            side_effect=RequestException("exception"),
        ):
            deregister_webhook(
                object, request_with_middleware, Subscription.objects.all()
            )

        messages = list(get_messages(request_with_middleware))
        self.assertEqual(len(messages), 1)
