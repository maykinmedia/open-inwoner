import json
import os
from datetime import date

from django.test import TestCase, override_settings
from django.utils.translation import gettext as _

import requests_mock
from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.logentry import LOG_ACTIONS

from ..models import HaalCentraalConfig
from .factories import ServiceFactory


def load_json_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "r") as f:
        return json.load(f)


def load_binary_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "rb") as f:
        return f.read()


@requests_mock.Mocker()
class TestPreSaveSignal(TestCase):
    def _setUpService(self):
        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/brp",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

    def _setUpMocks_v_2(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.999993847_2.0.json"),
        )

    def _setUpMocks_v_1_3(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen_1.3.yaml"),
        )
        m.get(
            "https://personen/api/brp/ingeschrevenpersonen/999993847?fields=naam,geboorte.datum",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.999993847_1.3.json"),
        )

    def test_signal_updates_users_data_when_logged_in_via_digid_v_2(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "Merel")
        self.assertEqual(updated_user[0].last_name, "Kooyman")
        self.assertEqual(updated_user[0].birthday, date(1982, 4, 10))
        self.assertTrue(updated_user[0].is_prepopulated)

    @override_settings(BRP_VERSION="1.3")
    def test_signal_updates_users_data_when_logged_in_via_digid_v_1_3(self, m):
        self._setUpMocks_v_1_3(m)
        self._setUpService()

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "Merel")
        self.assertEqual(updated_user[0].last_name, "Kooyman")
        self.assertEqual(updated_user[0].birthday, date(1982, 4, 10))
        self.assertTrue(updated_user[0].is_prepopulated)

    def test_user_is_not_updated_without_defining_service(self, m):
        self._setUpMocks_v_2(m)

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"

        with self.assertLogs() as captured:
            user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(
            captured.records[1].getMessage(),
            "no service defined for Haal Centraal",
        )
        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)
        self.assertFalse(updated_user[0].is_prepopulated)

    def test_user_is_not_updated_when_not_logged_in_via_digid(self, m):
        self._setUpMocks_v_2(m)

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.default
        )
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)
        self.assertFalse(updated_user[0].is_prepopulated)

    def test_empty_response_from_haalcentraal(self, m):
        self._setUpService()

        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=200,
            json={"personen": [], "type": "RaadpleegMetBurgerservicenummer"},
        )
        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)

    def test_user_is_not_updated_when_http_404(self, m):
        self._setUpService()

        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=404,
        )

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)
        self.assertFalse(updated_user[0].is_prepopulated)

    def test_user_is_not_updated_when_http_500(self, m):
        self._setUpService()

        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=500,
        )

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)
        self.assertFalse(updated_user[0].is_prepopulated)


class TestLogging(TestCase):
    @freeze_time("2021-10-18 13:00:00")
    @requests_mock.Mocker()
    def test_signal_updates_logging(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.999993847_2.0.json"),
        )

        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/brp",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"
        user.save()

        log_entry = TimelineLog.objects.filter(object_id=user.id)[0]

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, user.id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("data was retrieved from haal centraal"),
                "log_level": None,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": user.email,
            },
        )

    @requests_mock.Mocker()
    def test_single_entry_is_logged_when_there_is_an_error(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=500,
        )

        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/brp",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"
        user.save()

        log_entries = TimelineLog.objects.count()

        self.assertEqual(log_entries, 1)
