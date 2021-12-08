import json
import os
from datetime import date

from django.test import TestCase

import requests_mock

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import UserFactory

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


class TestPreSaveSignal(TestCase):
    @requests_mock.Mocker()
    def test_signal_updates_users_data_when_logged_in_via_digid(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999993847",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.999993847.json"),
        )

        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

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

    @requests_mock.Mocker()
    def test_user_is_not_updated_without_defining_service(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999993847",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.999993847.json"),
        )

        user = UserFactory(
            first_name="", last_name="", login_type=LoginTypeChoices.digid
        )
        user.bsn = "999993847"

        with self.assertLogs() as captured:
            user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(
            captured.records[0].getMessage(),
            "no service defined for Haal Centraal",
        )
        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)
        self.assertFalse(updated_user[0].is_prepopulated)

    @requests_mock.Mocker()
    def test_user_is_not_updated_when_not_logged_in_via_digid(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999993847",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.999993847.json"),
        )

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

    @requests_mock.Mocker()
    def test_user_is_not_updated_when_http_404(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999993847",
            status_code=404,
        )

        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

        user = UserFactory(first_name="", last_name="")
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)
        self.assertFalse(updated_user[0].is_prepopulated)

    @requests_mock.Mocker()
    def test_user_is_not_updated_when_http_500(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=500,
        )

        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

        user = UserFactory(first_name="", last_name="")
        user.bsn = "999993847"
        user.save()

        updated_user = User.objects.filter(email=user.email)

        self.assertEqual(updated_user[0].first_name, "")
        self.assertEqual(updated_user[0].last_name, "")
        self.assertEqual(updated_user[0].birthday, None)
        self.assertFalse(updated_user[0].is_prepopulated)
