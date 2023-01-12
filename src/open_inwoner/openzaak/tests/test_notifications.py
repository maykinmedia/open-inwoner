from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase

from open_inwoner.openzaak.api_models import Notification
from open_inwoner.openzaak.notifications import handle_notification
from open_inwoner.openzaak.tests.factories import NotificationFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"
DOCUMENTEN_ROOT = "https://documenten.nl/api/v1/"


class NotificationHandlerTestCase(TestCase):
    @patch("open_inwoner.openzaak.notifications.handle_zaak")
    def test_main_handler_routes_zaak_resource(self, mock_handle):
        notification = NotificationFactory(resource="zaak")

        handle_notification(notification)

        mock_handle.assert_called_once_with(notification)


class NotificationAPITestCase(APITestCase):
    url = reverse_lazy("openzaak-api:notifications-webhook")

    def test_api_requires_auth(self):
        self.fail("TODO")

    def test_api_validates_notification_members(self):
        raw_notification = {
            "kanaal": "zaken",
            "hoofdObject": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            # missing field resource
            # "resource": "zaak",
            "resourceUrl": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            "actie": "partial_update",
            "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
            "kenmerken": {},
        }
        response = self.client.post(self.url, raw_notification, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"resource": ["Dit veld is vereist."]})

    def test_api_validates_notification_kanaal(self):
        raw_notification = {
            # bad kanaal the view is not accepting
            "kanaal": "not_valid_kanaal",
            "hoofdObject": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            "resource": "zaak",
            "resourceUrl": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            "actie": "partial_update",
            "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
            "kenmerken": {},
        }
        response = self.client.post(self.url, raw_notification, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(), {"detail": "kanaal 'not_valid_kanaal' not accepted"}
        )

    @patch("open_inwoner.openzaak.api.views.handle_notification")
    def test_api_deserializes_raw_notification_and_calls_handler(self, mock_handle):
        raw_notification = {
            "kanaal": "zaken",
            "hoofdObject": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            "resource": "zaak",
            "resourceUrl": f"{ZAKEN_ROOT}/zaken/uuid-0001",
            "actie": "partial_update",
            "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
            "kenmerken": {
                "bronorganisatie": "100000009",
                "zaaktype": f"{CATALOGI_ROOT}/zaaktypes/uuid-0002",
                "vertrouwelijkheidaanduiding": "openbaar",
            },
        }
        response = self.client.post(self.url, raw_notification, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        mock_handle.assert_called_once()
        notification = mock_handle.call_args.args[0]
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.hoofd_object, raw_notification["hoofdObject"])
