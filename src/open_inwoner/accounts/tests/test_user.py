from datetime import date

from django.test import TestCase

from freezegun import freeze_time

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.utils.hash import generate_email_from_string

from ...plans.tests.factories import PlanFactory
from ..models import User
from .factories import UserFactory


class UserTests(TestCase):
    def test_get_full_name(self):
        user = User(first_name="Foo", infix="de", last_name="Bar")
        self.assertEqual(user.get_full_name(), "Foo de Bar")

        user = User(first_name="Foo", infix="", last_name="Bar")
        self.assertEqual(user.get_full_name(), "Foo Bar")

        user = User(first_name="", infix="de", last_name="Bar")
        self.assertEqual(user.get_full_name(), "de Bar")

        user = User(first_name="", infix="", last_name="Bar")
        self.assertEqual(user.get_full_name(), "Bar")

        # use display_name instead of first_name
        user = User(first_name="Foo", display_name="Flexi", infix="de", last_name="Bar")
        self.assertEqual(user.get_full_name(), "Flexi de Bar")

        # spaces everywhere
        user = User(first_name="Foo", display_name="    ", infix="de", last_name="Bar")
        self.assertEqual(user.get_full_name(), "Foo de Bar")

        user = User(
            first_name="  ",
            display_name="  ",
            infix="  ",
            last_name="  ",
            email="foo@bar.nl",
        )
        self.assertEqual(user.get_full_name(), "")

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

    def test_plan_contact_new_count_methods(self):
        owner = UserFactory()
        plan_1 = PlanFactory(created_by=owner)
        plan_2 = PlanFactory(created_by=owner)

        user = UserFactory()
        self.assertEqual(0, user.get_plan_contact_new_count())

        plan_1.plan_contacts.add(user)
        self.assertEqual(1, user.get_plan_contact_new_count())

        plan_2.plan_contacts.add(user)
        self.assertEqual(2, user.get_plan_contact_new_count())

        user.clear_plan_contact_new_count()
        self.assertEqual(0, user.get_plan_contact_new_count())
