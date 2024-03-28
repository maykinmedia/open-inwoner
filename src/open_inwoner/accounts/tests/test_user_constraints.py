from django.db import IntegrityError, transaction
from django.test import TestCase

from open_inwoner.accounts.choices import LoginTypeChoices

from .factories import UserFactory


class UserIdentifierConstraintTests(TestCase):
    def test_unique_email_when_login_default(self):
        UserFactory(email="foo@example.com", login_type=LoginTypeChoices.default)
        UserFactory(email="bar@example.com", login_type=LoginTypeChoices.default)

        with self.assertRaises(IntegrityError):
            UserFactory(email="foo@example.com", login_type=LoginTypeChoices.default)

    def test_not_unique_email_when_login_not_default(self):
        UserFactory(email="foo@example.com", login_type=LoginTypeChoices.default)

        UserFactory(email="foo@example.com", login_type=LoginTypeChoices.digid)
        UserFactory(email="foo@example.com", login_type=LoginTypeChoices.eherkenning)
        UserFactory(email="foo@example.com", login_type=LoginTypeChoices.oidc)

    def test_unique_bsn_when_login_digid(self):
        UserFactory(bsn="123456782", login_type=LoginTypeChoices.digid)
        UserFactory(bsn="123456783", login_type=LoginTypeChoices.digid)

        with self.assertRaises(IntegrityError):
            UserFactory(bsn="123456782", login_type=LoginTypeChoices.digid)

    def test_unique_oidc_id_when_login_oidc(self):
        UserFactory(oidc_id="1234", login_type=LoginTypeChoices.oidc)
        UserFactory(oidc_id="1235", login_type=LoginTypeChoices.oidc)

        with self.assertRaises(IntegrityError):
            UserFactory(oidc_id="1234", login_type=LoginTypeChoices.oidc)

    def test_unique_kvk_when_login_eherkenning(self):
        UserFactory(kvk="12345678", login_type=LoginTypeChoices.eherkenning)
        UserFactory(kvk="12345679", login_type=LoginTypeChoices.eherkenning)

        with self.assertRaises(IntegrityError):
            UserFactory(kvk="12345678", login_type=LoginTypeChoices.eherkenning)

    def test_unique_rsin_when_login_herkenning(self):
        UserFactory(rsin="12345678", login_type=LoginTypeChoices.eherkenning)
        UserFactory(rsin="12345679", login_type=LoginTypeChoices.eherkenning)

        with self.assertRaises(IntegrityError):
            UserFactory(rsin="12345678", login_type=LoginTypeChoices.eherkenning)

    def test_not_both_kvk_and_rsin_when_login_eherkenning(self):
        with self.assertRaises(IntegrityError):
            UserFactory(
                kvk="12345678", rsin="12345678", login_type=LoginTypeChoices.eherkenning
            )

    def test_not_bsn_when_login_not_digid(self):
        for login_type in [
            LoginTypeChoices.default,
            LoginTypeChoices.eherkenning,
            LoginTypeChoices.oidc,
        ]:
            with self.subTest(login_type):
                # start transaction block because we're testing multiple IntegrityErrors
                with transaction.atomic():
                    with self.assertRaises(IntegrityError):
                        UserFactory(bsn="123456782", login_type=login_type)

    def test_not_rsin_when_login_not_eherkenning(self):
        for login_type in [
            LoginTypeChoices.default,
            LoginTypeChoices.digid,
            LoginTypeChoices.oidc,
        ]:
            with self.subTest(login_type):
                # start transaction block because we're testing multiple IntegrityErrors
                with transaction.atomic():
                    with self.assertRaises(IntegrityError):
                        UserFactory(rsin="12345678", login_type=login_type)

    def test_not_kvk_when_login_not_eherkenning(self):
        for login_type in [
            LoginTypeChoices.default,
            LoginTypeChoices.digid,
            LoginTypeChoices.oidc,
        ]:
            with self.subTest(login_type):
                # start transaction block because we're testing multiple IntegrityErrors
                with transaction.atomic():
                    with self.assertRaises(IntegrityError):
                        UserFactory(kvk="12345678", login_type=login_type)

    def test_not_oidc_id_when_login_not_oidc(self):
        for login_type in [
            LoginTypeChoices.default,
            LoginTypeChoices.digid,
            LoginTypeChoices.eherkenning,
        ]:
            with self.subTest(login_type):
                # start transaction block because we're testing multiple IntegrityErrors
                with transaction.atomic():
                    with self.assertRaises(IntegrityError):
                        UserFactory(oidc_id="12345678", login_type=login_type)

    def test_login_types_not_changed(self):
        """
        The constraints and tests depend on a known set of login_types,
         so make sure this suite fails if we ever change them.
        """
        self.assertEqual(
            LoginTypeChoices.values,
            [
                LoginTypeChoices.default,
                LoginTypeChoices.digid,
                LoginTypeChoices.eherkenning,
                LoginTypeChoices.oidc,
            ],
        )
