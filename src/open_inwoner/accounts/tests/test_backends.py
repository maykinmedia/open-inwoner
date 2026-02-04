from unittest.mock import patch

from django.contrib import auth
from django.core.exceptions import SuspiciousOperation
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from furl import furl
from mozilla_django_oidc_db.config import store_config

from eherkenning.backends import eHerkenningBackend
from open_inwoner.accounts.backends import EIDASOIDCBackend
from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.accounts.models import OpenIDEIDASConfig, User
from open_inwoner.utils.test import SessionMiddleware

from .factories import (
    UserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
)


class OIDCBackendTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "open_inwoner.accounts.backends.CustomOIDCBackend",
            "open_inwoner.accounts.backends.DigiDOIDCBackend",
            "open_inwoner.accounts.backends.EHerkenningOIDCBackend",
        ]
    )
    @patch("open_inwoner.accounts.backends.DigiDOIDCBackend.authenticate")
    def test_digid_oidc_selects_correct_backend(self, mock_authenticate):
        """
        Both the regular OIDC and eHerkenning backend should check if the request path matches
        their callback before trying to authenticate
        """
        mock_authenticate.return_value = self.user

        init_response = self.client.get(reverse("digid_oidc:init"))

        assert "oidc_states" in self.client.session

        state = furl(init_response["Location"]).query.params["state"]
        nonce = self.client.session["oidc_states"][state]["nonce"]
        # set up a request
        callback_request = RequestFactory().get(
            reverse("digid_oidc:callback"),
            {"state": state, "nonce": nonce},
        )
        callback_request.session = self.client.session
        store_config(callback_request)

        result = auth.authenticate(callback_request)

        self.assertEqual(result, self.user)
        # django keeps track of which backend was used to authenticate
        self.assertEqual(
            result.backend, "open_inwoner.accounts.backends.DigiDOIDCBackend"
        )

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "open_inwoner.accounts.backends.DigiDOIDCBackend",
            "open_inwoner.accounts.backends.EHerkenningOIDCBackend",
            "open_inwoner.accounts.backends.CustomOIDCBackend",
        ]
    )
    @patch(
        "mozilla_django_oidc_db.backends.BaseBackend.authenticate",
        side_effect=Exception,
    )
    @patch("open_inwoner.accounts.backends.CustomOIDCBackend.authenticate")
    def test_admin_oidc_selects_correct_backend(
        self, mock_authenticate, mock_digid_eherkenning_authenticate
    ):
        """
        Both the DigiD and eHerkenning backend should check if the request path matches
        their callback before trying to authenticate
        """
        mock_authenticate.return_value = self.user
        init_response = self.client.get(reverse("oidc_authentication_init"))
        assert "oidc_states" in self.client.session
        state = furl(init_response["Location"]).query.params["state"]
        nonce = self.client.session["oidc_states"][state]["nonce"]
        # set up a request
        callback_request = RequestFactory().get(
            reverse("oidc_authentication_callback"),
            {"state": state, "nonce": nonce},
        )
        callback_request.session = self.client.session
        store_config(callback_request)

        result = auth.authenticate(callback_request)

        self.assertEqual(result, self.user)
        self.assertEqual(
            result.backend, "open_inwoner.accounts.backends.CustomOIDCBackend"
        )


class EHerkenningSAMLBackendTestCase(TestCase):
    def setUp(self):
        self.user = eHerkenningUserFactory()
        self.vestiging_user = eHerkenningVestigingUserFactory(kvk=self.user.kvk)

    def make_request_with_session(self):
        request = RequestFactory().get("/")
        middleware = SessionMiddleware(get_response=lambda r: None)
        middleware.process_request(request)
        request.session.save()  # Save to trigger session creation
        return request

    def test_kvk_claim_without_vestigingen_claim_returns_kvk_user(self):
        backend = eHerkenningBackend()
        request = self.make_request_with_session()
        context = EHerkenningSessionContext(request)

        user, created = backend.get_or_create_user(
            request,
            None,
            saml_attributes={
                "urn:etoegang:core:LegalSubjectID": [
                    {
                        "NameID": {
                            "NameQualifier": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                            "value": self.user.kvk,
                        }
                    },
                ]
            },
        )

        self.assertEqual(user, self.user)
        self.assertFalse(created)
        self.assertFalse(context.is_branch_restricted())

    def test_kvk_claim_with_vestigingen_claim_returns_vestiging_user(self):
        backend = eHerkenningBackend()
        request = self.make_request_with_session()
        context = EHerkenningSessionContext(request)

        user, created = backend.get_or_create_user(
            request,
            None,
            saml_attributes={
                "urn:etoegang:core:LegalSubjectID": [
                    {
                        "NameID": {
                            "NameQualifier": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                            "value": self.vestiging_user.kvk,
                        },
                    },
                ],
                "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr": self.vestiging_user.vestiging,
            },
        )

        self.assertEqual(user, self.vestiging_user)
        self.assertFalse(created)
        self.assertTrue(context.is_branch_restricted())

    def test_kvk_claim_without_vestigingen_claim_creates_kvk_user(self):
        User.objects.all().delete()
        backend = eHerkenningBackend()
        request = self.make_request_with_session()
        context = EHerkenningSessionContext(request)

        user, created = backend.get_or_create_user(
            request,
            None,
            saml_attributes={
                "urn:etoegang:core:LegalSubjectID": [
                    {
                        "NameID": {
                            "NameQualifier": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                            "value": "12345678",
                        }
                    },
                ]
            },
        )

        user = User.objects.get()
        self.assertEqual(user.kvk, "12345678")
        self.assertEqual(user.vestiging, "")
        self.assertTrue(created)
        self.assertFalse(context.is_branch_restricted())

    def test_kvk_claim_with_vestigingen_claim_creates_vestiging_user(self):
        User.objects.all().delete()
        backend = eHerkenningBackend()
        request = self.make_request_with_session()
        context = EHerkenningSessionContext(request)

        user, created = backend.get_or_create_user(
            request,
            None,
            saml_attributes={
                "urn:etoegang:core:LegalSubjectID": [
                    {
                        "NameID": {
                            "NameQualifier": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                            "value": "12345678",
                        },
                    },
                ],
                "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr": "123456789012",
            },
        )

        user = User.objects.get()
        self.assertEqual(user.kvk, "12345678")
        self.assertEqual(user.vestiging, "123456789012")
        self.assertTrue(created)
        self.assertTrue(context.is_branch_restricted())


class EIDASOIDCBackendTest(TestCase):
    def setUp(self):
        self.config = OpenIDEIDASConfig.get_solo()
        self.config.pseudo_identifier_claim = ["pseudo_id"]
        self.config.natural_person_bsn_identifier_claim = ["bsn"]
        self.config.natural_person_first_name_claim = ["first_name"]
        self.config.natural_person_family_name_claim = ["family_name"]
        self.config.company_name_claim = ["company_name"]
        self.config.legal_entity_identifier_claim = ["legal_entity"]
        self.config.save()

        self.backend = EIDASOIDCBackend()

    def test_create_user_with_empty_claims_raises_error(self):
        with self.assertRaises(SuspiciousOperation) as context:
            self.backend.create_user({})

        self.assertIn("pseudo identifier", str(context.exception))

    def test_create_user_with_only_pseudo_id_raises_error(self):
        with self.assertRaises(SuspiciousOperation) as context:
            self.backend.create_user({"pseudo_id": "test-pseudo-id"})

        self.assertIn("identifying information", str(context.exception))

    def test_create_user_without_pseudo_id_raises_error(self):
        with self.assertRaises(SuspiciousOperation) as context:
            self.backend.create_user({"first_name": "John", "family_name": "Doe"})

        self.assertIn("pseudo identifier", str(context.exception))

    def test_create_user_with_incomplete_company_claims_raises_error(self):
        """
        Incomplete company claims (only one of company_name or legal_entity)
        should raise a SuspiciousOperation error.
        Both company_name AND legal_entity are required together for company user.
        """
        # Only company name, no legal entity - should raise error
        with self.assertRaises(SuspiciousOperation) as context:
            self.backend.create_user(
                {"pseudo_id": "test-pseudo-id-1", "company_name": "Test Company"}
            )

        self.assertIn("company name and legal entity ID", str(context.exception))
        self.assertIn("company_name=present", str(context.exception))
        self.assertIn("legal_entity_id=missing", str(context.exception))

        # Only legal entity, no company name - should raise error
        with self.assertRaises(SuspiciousOperation) as context:
            self.backend.create_user(
                {"pseudo_id": "test-pseudo-id-2", "legal_entity": "12345678"}
            )

        self.assertIn("company name and legal entity ID", str(context.exception))
        self.assertIn("company_name=missing", str(context.exception))
        self.assertIn("legal_entity_id=present", str(context.exception))

    def test_create_user_with_person_bsn_claims(self):
        claims = {
            "pseudo_id": "test-pseudo-bsn",
            "bsn": "123456789",
            "first_name": "John",
            "family_name": "Doe",
        }

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertEqual(user.eidas_pseudo_id, "test-pseudo-bsn")
        self.assertEqual(user.bsn, "123456789")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_person_bsn)
        self.assertTrue(user.email)  # Should have generated email

    def test_create_user_with_person_pseudo_id_only_claims(self):
        claims = {
            "pseudo_id": "test-pseudo-only",
            "first_name": "Jane",
            "family_name": "Smith",
        }

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertEqual(user.eidas_pseudo_id, "test-pseudo-only")
        self.assertEqual(user.bsn, "")
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_person_pseudo_id)
        self.assertTrue(user.email)

    def test_create_user_with_person_missing_first_name(self):
        claims = {"pseudo_id": "test-pseudo-no-first", "family_name": "Doe"}

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertEqual(user.eidas_pseudo_id, "test-pseudo-no-first")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_person_pseudo_id)

    def test_create_user_with_person_missing_family_name(self):
        claims = {"pseudo_id": "test-pseudo-no-last", "first_name": "John"}

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertEqual(user.eidas_pseudo_id, "test-pseudo-no-last")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_person_pseudo_id)

    def test_create_user_with_company_claims(self):
        claims = {
            "pseudo_id": "test-pseudo-company",
            "company_name": "Acme Corporation",
            "legal_entity": "NL123456789B01",
        }

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertEqual(user.eidas_pseudo_id, "test-pseudo-company")
        self.assertEqual(user.company_name, "Acme Corporation")
        self.assertEqual(user.eidas_company_id, "NL123456789B01")
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_company)
        self.assertTrue(user.email)

    def test_create_user_prioritizes_company_over_person(self):
        claims = {
            "pseudo_id": "test-pseudo-both",
            "company_name": "Test Company",
            "legal_entity": "12345678",
            "first_name": "John",
            "family_name": "Doe",
            "bsn": "987654321",
        }

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_company)
        self.assertEqual(user.company_name, "Test Company")
        self.assertEqual(user.eidas_company_id, "12345678")
        # Person fields should not be set
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.bsn, "")

    def test_update_user_with_valid_person_bsn_claims(self):
        user = UserFactory.create(
            eidas_pseudo_id="test-pseudo-update",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
            first_name="OldFirst",
            last_name="OldLast",
        )

        claims = {
            "pseudo_id": "test-pseudo-update",
            "bsn": "675153128",
            "first_name": "NewFirst",
            "family_name": "NewLast",
        }

        updated_user = self.backend.update_user(user, claims)

        # Refresh from database to verify changes
        user.refresh_from_db()

        self.assertIsNotNone(updated_user)
        self.assertEqual(user.bsn, "675153128")
        self.assertEqual(user.first_name, "NewFirst")
        self.assertEqual(user.last_name, "NewLast")
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_person_bsn)

    def test_update_user_with_valid_company_claims(self):
        user = UserFactory.create(
            eidas_pseudo_id="test-pseudo-company-update",
            login_type=LoginTypeChoices.eidas_company,
            company_name="Old Company",
        )

        claims = {
            "pseudo_id": "test-pseudo-company-update",
            "company_name": "New Company",
            "legal_entity": "99999999",
        }

        updated_user = self.backend.update_user(user, claims)

        user.refresh_from_db()

        self.assertIsNotNone(updated_user)
        self.assertEqual(user.company_name, "New Company")
        self.assertEqual(user.eidas_company_id, "99999999")
        self.assertEqual(user.login_type, LoginTypeChoices.eidas_company)

    def test_update_user_with_invalid_claims_returns_user_unchanged(self):
        user = UserFactory.create(
            eidas_pseudo_id="test-pseudo-invalid",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
            first_name="Original",
        )

        # Claims with only pseudo_id (no identifying info)
        with self.assertRaises(SuspiciousOperation):
            self.backend.update_user(user, {"pseudo_id": "test-pseudo-invalid"})

        # Verify user wasn't changed
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Original")

    def test_update_user_without_pseudo_id_raises_error(self):
        user = UserFactory.create(eidas_pseudo_id="test-pseudo")

        with self.assertRaises(SuspiciousOperation):
            self.backend.update_user(user, {"first_name": "John", "family_name": "Doe"})

    def test_create_user_with_nested_claim_paths(self):
        self.config.pseudo_identifier_claim = ["nested", "pseudo", "id"]
        self.config.natural_person_first_name_claim = ["person", "firstName"]
        self.config.natural_person_family_name_claim = ["person", "familyName"]
        self.config.save()

        claims = {
            "nested": {"pseudo": {"id": "nested-pseudo-id"}},
            "person": {"firstName": "John", "familyName": "Doe"},
        }

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertEqual(user.eidas_pseudo_id, "nested-pseudo-id")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

    def test_create_user_generates_unique_email_from_pseudo_id(self):
        """Email should be generated from pseudo_id"""
        claims = {
            "pseudo_id": "unique-pseudo-123",
            "first_name": "Test",
            "family_name": "User",
        }

        user = self.backend.create_user(claims)

        self.assertIsNotNone(user)
        self.assertIn("@localhost", user.email)
        # Email should be deterministic based on pseudo_id
        self.assertTrue(user.email)

    def test_create_multiple_users_with_different_pseudo_ids(self):
        claims1 = {
            "pseudo_id": "user1-pseudo",
            "first_name": "User",
            "family_name": "One",
        }
        claims2 = {
            "pseudo_id": "user2-pseudo",
            "first_name": "User",
            "family_name": "Two",
        }

        user1 = self.backend.create_user(claims1)
        user2 = self.backend.create_user(claims2)

        self.assertIsNotNone(user1)
        self.assertIsNotNone(user2)
        self.assertNotEqual(user1.id, user2.id)
        self.assertEqual(user1.eidas_pseudo_id, "user1-pseudo")
        self.assertEqual(user2.eidas_pseudo_id, "user2-pseudo")

    def test_update_user_with_invalid_field_value_raises_error(self):
        user = UserFactory(
            eidas_pseudo_id="test-pseudo-validation",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
            first_name="Original",
        )

        claims = {
            "pseudo_id": "test-pseudo-validation",
            "first_name": "X" * 1024,  # Exceeds max_length=255
            "family_name": "Doe",
        }

        with self.assertRaises(SuspiciousOperation) as context:
            self.backend.update_user(user, claims)

        self.assertIn("validation error", str(context.exception))

        # Verify user wasn't changed
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Original")
