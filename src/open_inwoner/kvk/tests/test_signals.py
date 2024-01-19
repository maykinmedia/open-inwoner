import logging

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.translation import gettext as _

import requests_mock
from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.logentry import LOG_ACTIONS
from open_inwoner.utils.test import ClearCachesMixin

from ..client import KvKClient
from ..models import KvKConfig
from . import mocks

UserModel = get_user_model()


@requests_mock.Mocker()
class TestPreSaveSignal(ClearCachesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        config = KvKConfig(
            api_root="https://api.kvk.nl/test/api/v1",
            api_key="12345",
        )
        config.save()
        cls.kvk_client = KvKClient(config)

    def test_signal_updates_users_data_when_logged_in_via_eherkenning(self, m):
        m.get(
            self.kvk_client._build_url(
                f"{self.kvk_client.basisprofielen_endpoint}/69599084",
            ),
            json=mocks.basisprofiel_detail,
        )

        user = UserModel.eherkenning_objects.eherkenning_create("69599084")

        self.client.force_login(user=user)

        user.refresh_from_db()

        self.assertEqual(user.rsin, "857587973")
        self.assertTrue(user.is_prepopulated)

    def test_user_is_not_updated_when_not_logged_in_via_eherkenning(self, m):
        user = UserFactory(
            first_name="", infix="", last_name="", login_type=LoginTypeChoices.default
        )
        user.bsn = "69599084"
        user.save()

        user.refresh_from_db()

        self.assertEqual(user.rsin, "")
        self.assertFalse(user.is_prepopulated)

    def test_empty_response_from_kvk(self, m):
        m.get(
            self.kvk_client._build_url(
                f"{self.kvk_client.basisprofielen_endpoint}/69599084",
            ),
            json=mocks.empty,
        )

        user = UserModel.eherkenning_objects.eherkenning_create("69599084")

        user.refresh_from_db()

        self.assertEqual(user.rsin, "")
        self.assertFalse(user.is_prepopulated)

    def test_user_is_not_updated_when_http_404(self, m):
        m.get(
            self.kvk_client._build_url(
                f"{self.kvk_client.basisprofielen_endpoint}/69599084",
            ),
            status_code=404,
        )

        user = UserModel.eherkenning_objects.eherkenning_create("69599084")
        user.refresh_from_db()

        self.assertEqual(user.rsin, "")
        self.assertFalse(user.is_prepopulated)

    def test_user_is_not_updated_when_http_500(self, m):
        m.get(
            self.kvk_client._build_url(
                f"{self.kvk_client.basisprofielen_endpoint}/69599084",
            ),
            status_code=500,
        )

        user = UserModel.eherkenning_objects.eherkenning_create("69599084")
        user.refresh_from_db()

        self.assertEqual(user.rsin, "")
        self.assertFalse(user.is_prepopulated)


class TestLogging(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = KvKConfig(
            api_root="https://api.kvk.nl/test/api/v1",
            api_key="12345",
        )
        config.save()
        cls.kvk_client = KvKClient(config)

    @freeze_time("2021-10-18 13:00:00")
    @requests_mock.Mocker()
    def test_signal_updates_logging(self, m):
        m.get(
            self.kvk_client._build_url(
                f"{self.kvk_client.basisprofielen_endpoint}/69599084",
            ),
            json=mocks.basisprofiel_detail,
        )

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.eherkenning
        )
        user.kvk = "69599084"
        user.save()

        self.client.force_login(user=user)

        log_entry = TimelineLog.objects.filter(object_id=user.id)[2]

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.object_id, str(user.id))
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("data was retrieved from KvK API"),
                "log_level": logging.INFO,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": str(user),
            },
        )

    @requests_mock.Mocker()
    def test_single_entry_is_logged_when_there_is_an_error(self, m):
        m.get(
            self.kvk_client._build_url(
                f"{self.kvk_client.basisprofielen_endpoint}/69599084",
            ),
            status_code=500,
        )

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.eherkenning
        )
        user.kvk = "69599084"
        user.save()

        self.client.force_login(user=user)

        log_entries = TimelineLog.objects.count()

        # Login message + message to attempt KvK data retrieval
        self.assertEqual(log_entries, 2)
