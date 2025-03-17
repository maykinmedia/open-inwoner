from unittest import mock

from django.test import RequestFactory, TestCase

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
)
from open_inwoner.utils.test import SessionMiddleware


class EHerkenningSessionContextTests(TestCase):
    def setUp(self):
        self.user = eHerkenningUserFactory()
        self.vestiging_user = eHerkenningVestigingUserFactory(kvk=self.user.kvk)

    def make_request_with_session(self):
        request = RequestFactory().get("/")
        middleware = SessionMiddleware(get_response=lambda r: None)
        middleware.process_request(request)
        request.session.save()  # Save to trigger session creation
        return request

    def test_persisted_state_generates_expected_branch_restriction_state(self):
        for branch_restriction in (True, False):
            with self.subTest(branch_restriction):
                request = self.make_request_with_session()
                request.user = self.user

                context = EHerkenningSessionContext(request)
                context.persist_eherkenning_state_for_user(
                    user=self.user, is_branch_restricted=branch_restriction
                )

                self.assertEqual(context.is_branch_restricted(), branch_restriction)
                self.assertFalse(context.is_initial_branch_selection_done())

    def test_branch_restriction_check_fails_on_non_bool(self):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = EHerkenningSessionContext._expected_auth_backends()[0]

        for val in (1, "foo", object(), None):
            with self.subTest(val):
                request.session[
                    EHerkenningSessionContext.KVK_BRANCH_RESTRICTION_SESSION_KEY
                ] = val

                context = EHerkenningSessionContext(request)
                with self.assertRaises(ValueError) as ctx:
                    context.is_branch_restricted()

                self.assertEqual(
                    str(ctx.exception),
                    'session["kvk_has_branch_restriction"] must be bool',
                )

    def test_change_authenticated_user_raises_on_missing_backend(self):
        request = self.make_request_with_session()

        context = EHerkenningSessionContext(request)
        with self.assertRaises(ValueError) as ctx:
            context.change_authenticated_user(kvk=self.user.kvk, vestiging=None)

        self.assertEqual(
            str(ctx.exception),
            "The user in this session was not authenticated via the expected "
            "EHerkenning backends: open_inwoner.accounts.backends."
            "EHerkenningOIDCBackend, eherkenning.backends.eHerkenningBackend, "
            "eherkenning.mock.backends.eHerkenningBackend",
        )

    def test_change_authenticated_user_raises_on_incorrect_backend(self):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = "open_inwoner.accounts.backends.DigiDOIDCBackend"

        context = EHerkenningSessionContext(request)
        with self.assertRaises(ValueError) as ctx:
            context.change_authenticated_user(kvk=self.user.kvk, vestiging=None)

        self.assertEqual(
            str(ctx.exception),
            "The user in this session was not authenticated via the expected "
            "EHerkenning backends: open_inwoner.accounts.backends."
            "EHerkenningOIDCBackend, eherkenning.backends.eHerkenningBackend, "
            "eherkenning.mock.backends.eHerkenningBackend",
        )

    def test_change_authenticated_user_raises_on_non_eherkenning_user(self):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = EHerkenningSessionContext._expected_auth_backends()[0]
        request.user = DigidUserFactory()

        context = EHerkenningSessionContext(request)
        with self.assertRaises(ValueError) as ctx:
            context.change_authenticated_user(kvk=self.user.kvk, vestiging=None)

        self.assertEqual(str(ctx.exception), "User is not an eHerkenning user")

    def test_change_authenticated_user_with_branch_restriction_raises(
        self,
    ):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = EHerkenningSessionContext._expected_auth_backends()[0]
        request.user = self.user

        context = EHerkenningSessionContext(request)
        context._set_branch_restriction(True)

        with self.assertRaises(ValueError) as ctx:
            context.change_authenticated_user(
                kvk=self.user.kvk, vestiging=self.vestiging_user.vestiging
            )

        self.assertEqual(
            str(ctx.exception),
            "This session is branch restricted: you cannot switch "
            "to a different eherkenning user",
        )
        self.assertEqual(request.user, self.user)

    def test_change_authenticated_user_raises_on_target_user_with_different_kvk(self):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = EHerkenningSessionContext._expected_auth_backends()[0]
        request.user = self.user
        different_kvk_user = eHerkenningUserFactory(kvk="38804926")

        context = EHerkenningSessionContext(request)
        with self.assertRaises(ValueError) as ctx:
            context.change_authenticated_user(
                kvk=different_kvk_user.kvk, vestiging=None
            )

        self.assertEqual(
            str(ctx.exception),
            "You cannot change the authenticated user to the rechtspersoon or "
            "vestiging of a different kvk number",
        )
        self.assertEqual(request.user, self.user)

    def test_change_authenticated_user_from_kvk_to_kvk_and_vestiging(self):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = EHerkenningSessionContext._expected_auth_backends()[0]
        request.user = self.user

        context = EHerkenningSessionContext(request)
        context.change_authenticated_user(
            kvk=self.user.kvk, vestiging=self.vestiging_user.vestiging
        )

        self.assertEqual(request.user, self.vestiging_user)
        self.assertEqual(
            request.session["_auth_user_backend"],
            EHerkenningSessionContext._expected_auth_backends()[0],
        )
        self.assertFalse(context.is_branch_restricted())
        self.assertFalse(context.is_initial_branch_selection_done())

    def test_change_authenticated_user_from_vestiging_and_kvk_to_only_kvk(self):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = EHerkenningSessionContext._expected_auth_backends()[0]
        request.user = self.vestiging_user

        context = EHerkenningSessionContext(request)
        context.change_authenticated_user(kvk=self.user.kvk, vestiging=None)

        self.assertEqual(request.user, self.user)
        self.assertEqual(
            request.session["_auth_user_backend"],
            EHerkenningSessionContext._expected_auth_backends()[0],
        )
        self.assertFalse(context.is_branch_restricted())
        self.assertFalse(context.is_initial_branch_selection_done())

    def test_change_authenticated_user_to_same_user_does_not_mutate_session(self):
        request = self.make_request_with_session()
        request.session[
            "_auth_user_backend"
        ] = EHerkenningSessionContext._expected_auth_backends()[0]
        request.user = self.user

        context = EHerkenningSessionContext(request)

        with mock.patch(
            "open_inwoner.accounts.eherkenning_session.django_logout"
        ) as mock_logout:
            context.change_authenticated_user(kvk=self.user.kvk, vestiging=None)

        mock_logout.assert_not_called()
        self.assertEqual(request.user, self.user)
        self.assertEqual(
            request.session["_auth_user_backend"],
            EHerkenningSessionContext._expected_auth_backends()[0],
        )
        self.assertFalse(context.is_branch_restricted())
        self.assertFalse(context.is_initial_branch_selection_done())

    def test_change_authenticated_user_maintains_branch_restriction_and_backend(self):
        for expected_backend in EHerkenningSessionContext._expected_auth_backends():

            with self.subTest(expected_backend):
                request = self.make_request_with_session()
                request.session["_auth_user_backend"] = expected_backend
                request.user = self.user
                context = EHerkenningSessionContext(request)
                context._set_branch_restriction(False)

                context.change_authenticated_user(
                    kvk=self.vestiging_user.kvk,
                    vestiging=self.vestiging_user.vestiging,
                )

                self.assertEqual(request.user, self.vestiging_user)
                self.assertEqual(
                    request.session["_auth_user_backend"],
                    expected_backend,
                )
                self.assertEqual(context.is_branch_restricted(), False)
                self.assertFalse(context.is_initial_branch_selection_done())
