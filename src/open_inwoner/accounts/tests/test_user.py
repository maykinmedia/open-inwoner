from datetime import date

from django.test import TestCase

from freezegun import freeze_time

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.utils.hash import generate_email_from_string

from ..models import User
from .factories import UserFactory


class UserTests(TestCase):
    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_same_day(self):
        with freeze_time("1990-07-07"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 31)

    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_day_before(self):
        with freeze_time("1990-07-08"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 30)

    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_day_after(self):
        with freeze_time("1990-07-06"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 31)

    @freeze_time("2021-07-07 12:00:00")
    def test_get_age_young(self):
        with freeze_time("2014-01-07"):
            user = User(birthday=date.today())
        self.assertEqual(user.get_age(), 7)

    def test_require_necessary_fields(self):
        user = UserFactory()
        self.assertFalse(user.require_necessary_fields())

    def test_require_necessary_fields_digid(self):
        user = UserFactory(login_type=LoginTypeChoices.digid, email="john@smith.nl")
        self.assertFalse(user.require_necessary_fields())

    def test_require_necessary_fields_digid_no_first_name(self):
        user = UserFactory(login_type=LoginTypeChoices.digid, first_name="")
        self.assertTrue(user.require_necessary_fields())

    def test_require_necessary_fields_digid_no_last_name(self):
        user = UserFactory(login_type=LoginTypeChoices.digid, last_name="")
        self.assertTrue(user.require_necessary_fields())

    def test_require_necessary_fields_digid_openinwoner_email(self):
        bsn = "123456789"
        oip_email = generate_email_from_string(bsn)
        user = UserFactory(login_type=LoginTypeChoices.digid, bsn=bsn, email=oip_email)
        self.assertTrue(user.require_necessary_fields())

    def test_require_necessary_fields_oidc(self):
        user = UserFactory(
            login_type=LoginTypeChoices.oidc, email="test@maykinmedia.nl"
        )
        self.assertFalse(user.require_necessary_fields())

    def test_require_necessary_fields_oidc_no_email(self):
        user = UserFactory(login_type=LoginTypeChoices.oidc, email="")
        self.assertTrue(user.require_necessary_fields())

    def test_require_necessary_fields_oidc_openinwoner_email(self):
        user = UserFactory(
            login_type=LoginTypeChoices.oidc, email="test@example.org", oidc_id="test"
        )
        self.assertTrue(user.require_necessary_fields())
