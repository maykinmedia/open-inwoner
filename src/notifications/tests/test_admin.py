from django.contrib import admin as django_admin
from django.test import RequestFactory, TestCase

from zgw_consumers.constants import APITypes
from zgw_consumers.models.services import Service

from notifications.admin import NotificationRecordAdmin
from notifications.models import (
    NotificationRecord,
    NotificationsAPIConfig,
    Subscription,
)


class NotificationRecordAdminSearchTestCase(TestCase):
    """Tests for full-text search on the (JSON) payload field in the admin."""

    @classmethod
    def setUpTestData(cls):
        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
        )
        config = NotificationsAPIConfig.objects.create(
            notifications_api_service=service
        )
        cls.subscription = Subscription.objects.create(
            notifications_api_config=config,
            callback_url="https://example.com/callback",
            client_id="test_client",
            secret="test_secret",
            channels=["zaken"],
        )

        cls.matching_record = NotificationRecord.objects.create(
            subscription=cls.subscription,
            kanaal="zaken",
            payload={
                "resource": "zaak",
                "actie": "update",
                "kenmerken": {
                    "zaaktype": "https://example.com/zaaktypen/unieke-waarde-123",
                },
            },
        )
        cls.other_record = NotificationRecord.objects.create(
            subscription=cls.subscription,
            kanaal="besluiten",
            payload={"resource": "besluit", "actie": "create"},
        )

    def setUp(self):
        super().setUp()
        self.model_admin = NotificationRecordAdmin(
            NotificationRecord, django_admin.site
        )
        self.request = RequestFactory().get("/")

    def test_payload_is_a_search_field(self):
        self.assertIn("payload", self.model_admin.search_fields)

    def test_search_matches_value_nested_inside_payload(self):
        queryset, _ = self.model_admin.get_search_results(
            self.request,
            NotificationRecord.objects.all(),
            "unieke-waarde-123",
        )

        self.assertEqual(list(queryset), [self.matching_record])

    def test_search_does_not_match_unrelated_payload(self):
        queryset, _ = self.model_admin.get_search_results(
            self.request,
            NotificationRecord.objects.all(),
            "unieke-waarde-123",
        )

        self.assertNotIn(self.other_record, queryset)

    def test_search_is_case_insensitive(self):
        queryset, _ = self.model_admin.get_search_results(
            self.request,
            NotificationRecord.objects.all(),
            "UNIEKE-WAARDE-123",
        )

        self.assertEqual(list(queryset), [self.matching_record])
