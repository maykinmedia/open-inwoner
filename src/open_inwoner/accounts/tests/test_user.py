from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.plans.tests.factories import PlanFactory
from open_inwoner.utils.hash import generate_email_from_string

from .factories import UserFactory, eHerkenningVestigingUserFactory


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
        user = User(first_name="Foo", infix="de", last_name="Bar")
        self.assertEqual(user.get_full_name(), "Foo de Bar")

        # spaces everywhere
        user = User(first_name="Foo", infix="de", last_name="Bar")
        self.assertEqual(user.get_full_name(), "Foo de Bar")

        user = User(
            first_name="  ",
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

    def test_has_usable_email(self):
        user_ok1 = UserFactory(email="foo@bar.baz")
        self.assertTrue(user_ok1.has_usable_email)

        user_ok2 = UserFactory(email="test@example.com")
        self.assertTrue(user_ok2.has_usable_email)

        self.assertFalse(UserFactory(email="").has_usable_email)

        # @example.org is used as placeholder
        self.assertFalse(UserFactory(email="test@example.org").has_usable_email)

        # @localhost occurs in some old code
        self.assertFalse(UserFactory(email="test@localhost").has_usable_email)

        actual = set(User.objects.having_usable_email())
        self.assertEqual(actual, {user_ok1, user_ok2})

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

    def test_phonenumber_alternative_requires_primary_phonenumber(self):
        user = UserFactory(phonenumber="")

        with self.assertRaises(IntegrityError):
            user.phonenumber_alternative = "0612345678"
            user.save()

    def test_phonenumber_alternative_differs_from_non_empty_primary_phonenumber(self):
        user = UserFactory(phonenumber="612345678")

        with self.assertRaises(IntegrityError):
            user.phonenumber_alternative = user.phonenumber
            user.save()

    def test_allow_both_phonenumbers_empty(self):
        user = UserFactory()

        user.phonenumber = ""
        user.phonenumber_alternative = ""
        user.save()

    def test_eherkenning_user_requires_kvk(self):
        with self.assertRaises(IntegrityError):
            UserFactory(login_type=LoginTypeChoices.eherkenning, kvk="")

    def test_vestiging_validation_must_be_11_digits(self):
        for invalid_vestiging in tuple(str("1" * i) for i in range(1, 11)):
            with self.subTest(invalid_vestiging):
                user = eHerkenningVestigingUserFactory(vestiging=invalid_vestiging)
                with self.assertRaises(ValidationError):
                    user.full_clean()

    def test_vestiging_validation_must_be_numeric(self):
        for invalid_vestiging in tuple(str(c * 11) for c in ("a", "-", " ")):
            with self.subTest(invalid_vestiging):
                user = eHerkenningVestigingUserFactory(vestiging=invalid_vestiging)
                with self.assertRaises(ValidationError):
                    user.full_clean()

    def test_vestiging_requires_kvk(self):
        with self.assertRaises(IntegrityError):
            eHerkenningVestigingUserFactory(kvk="", vestiging="123456789012")

    def test_vestiging_can_be_empty(self):
        user = UserFactory(kvk="12345678", vestiging="")
        self.assertTrue(user)

    def test_vestiging_must_be_unique_per_kvk(self):
        eHerkenningVestigingUserFactory(vestiging="123456789012")
        with self.assertRaises(IntegrityError):
            eHerkenningVestigingUserFactory(vestiging="123456789012")

    def test_kvk_without_vestiging_must_be_unique(self):
        eHerkenningVestigingUserFactory(kvk="12345678", vestiging="")
        with self.assertRaises(IntegrityError):
            eHerkenningVestigingUserFactory(kvk="12345678", vestiging="")
