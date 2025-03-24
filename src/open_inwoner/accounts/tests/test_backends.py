from unittest.mock import patch

from django.contrib import auth
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from furl import furl
from mozilla_django_oidc_db.config import store_config

from eherkenning.backends import eHerkenningBackend
from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.accounts.models import User
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
                "urn:etoegang:1.11:attribute-represented:KvKnr": [self.user.kvk]
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
                "urn:etoegang:1.11:attribute-represented:KvKnr": [
                    self.vestiging_user.kvk
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
                "urn:etoegang:1.11:attribute-represented:KvKnr": ["12345678"]
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
                "urn:etoegang:1.11:attribute-represented:KvKnr": ["12345678"],
                "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr": "123456789012",
            },
        )

        user = User.objects.get()
        self.assertEqual(user.kvk, "12345678")
        self.assertEqual(user.vestiging, "123456789012")
        self.assertTrue(created)
        self.assertTrue(context.is_branch_restricted())
