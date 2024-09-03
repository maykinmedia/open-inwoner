from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase

import requests_mock
from requests.exceptions import RequestException
from zgw_consumers.constants import APITypes
from zgw_consumers.models.services import Service

from ..admin import register_webhook
from ..models import NotificationsAPIConfig, Subscription
from .utils import make_request_with_middleware


class NotificationsAPIWebhookTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
            oas="http://some-api-root/api/v1/schema/openapi.yaml",
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
