from django.test import TestCase

import requests_mock
from freezegun import freeze_time
from log_outgoing_requests.models import OutgoingRequestsLog

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.test import ClearCachesMixin

from .mixins import HaalCentraalMixin


@freeze_time("2021-10-18 13:00:00")
@requests_mock.Mocker()
class TestPreSaveSignal(ClearCachesMixin, HaalCentraalMixin, TestCase):
    def test_outgoing_requests_are_logged_and_saved(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        self.assertFalse(OutgoingRequestsLog.objects.exists())

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"

        with self.assertLogs() as captured:
            user.save()

        logs_messages = [record.getMessage() for record in captured.records]
        saved_logs = OutgoingRequestsLog.objects.filter(
            url="https://personen/api/brp/personen"
        )

        self.assertIn("Outgoing request", logs_messages)
        self.assertTrue(saved_logs.exists())
