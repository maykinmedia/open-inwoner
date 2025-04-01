from django.conf import settings
from django.contrib.auth import login as django_login, logout as django_logout
from django.http import HttpRequest

from open_inwoner.accounts.models import User


class EHerkenningSessionContext:
    """Helper service to manage eHerkenning state in a request session."""

    _request: HttpRequest
    KVK_BRANCH_RESTRICTION_SESSION_KEY = "kvk_has_branch_restriction"
    KVK_INITIAL_BRANCH_SELECTION_DONE_KEY = "kvk_initial_branch_selection_done"

    def __init__(self, request: HttpRequest):
        self._request = request

    @classmethod
    def _expected_auth_backends(cls) -> tuple[str, ...]:
        expected_backends = (
            "open_inwoner.accounts.backends.EHerkenningOIDCBackend",
            "eherkenning.backends.eHerkenningBackend",
        )
        mock_backends = ("eherkenning.mock.backends.eHerkenningBackend",)

        return expected_backends + tuple(
            backend
            for backend in mock_backends
            if backend in settings.AUTHENTICATION_BACKENDS
        )

    @staticmethod
    def assert_valid_eherkenning_user(user: User) -> None:
        if (
            not isinstance(user, User)
            or (not user.is_eherkenning_user)
            or (not user.kvk)
        ):
            raise ValueError("User is not an eHerkenning user")

    @staticmethod
    def assert_valid_eherkenning_request(request: HttpRequest) -> None:
        if (
            request.session.get("_auth_user_backend", None)
            not in EHerkenningSessionContext._expected_auth_backends()
        ):
            raise ValueError(
                "The user in this session was not authenticated via the expected "
                f"EHerkenning backends: {', '.join(EHerkenningSessionContext._expected_auth_backends())}"
            )

    def _set_session_flag(self, key: str, flag: bool) -> None:
        if not isinstance(flag, bool):
            raise ValueError("`flag` must be a boolean")

        self._request.session[key] = flag
        self._request.session.save()

    def _get_session_flag(self, key: str) -> bool:
        if key not in self._request.session:
            return False

        flag = self._request.session.get(
            key,
        )
        if not isinstance(flag, bool):
            raise ValueError(f'session["{key}"] must be bool')

        return flag

    def _set_initial_branch_selection(self, done: bool) -> None:
        self._set_session_flag(self.KVK_INITIAL_BRANCH_SELECTION_DONE_KEY, done)

    def _set_branch_restriction(self, restriction: bool) -> None:
        self._request.session[self.KVK_BRANCH_RESTRICTION_SESSION_KEY] = bool(
            restriction
        )
        self._request.session.save()

    def is_branch_restricted(self) -> bool:
        return self._get_session_flag(self.KVK_BRANCH_RESTRICTION_SESSION_KEY)

    def is_initial_branch_selection_done(self) -> bool:
        return self._get_session_flag(self.KVK_INITIAL_BRANCH_SELECTION_DONE_KEY)

    def mark_initial_branch_selection_done(self) -> None:
        self._set_initial_branch_selection(True)

    def persist_eherkenning_state_for_user(
        self,
        *,
        user: User,
        is_branch_restricted: bool,
        initial_branch_selection_done: bool = False,
    ) -> None:
        # Note we do not validate the authentication backend here because this likely to
        # be called _within_ an authentication backend handler and thus the user will
        # not yet be authenticated.
        self.assert_valid_eherkenning_user(user)
        self._set_session_flag(
            self.KVK_BRANCH_RESTRICTION_SESSION_KEY, is_branch_restricted
        )
        self._set_session_flag(
            self.KVK_INITIAL_BRANCH_SELECTION_DONE_KEY, initial_branch_selection_done
        )

    def change_authenticated_user(
        self,
        *,
        kvk: str,
        vestiging: str | None,
    ) -> None:
        self.assert_valid_eherkenning_request(self._request)
        self.assert_valid_eherkenning_user(self._request.user)

        if self.is_branch_restricted():
            raise ValueError(
                "This session is branch restricted: you cannot switch to a different "
                "eherkenning user"
            )

        if self._request.user.kvk != kvk:
            raise ValueError(
                "You cannot change the authenticated user to the rechtspersoon or "
                "vestiging of a different kvk number"
            )

        try:
            target_user = User.eherkenning_objects.get_by_kvk_and_vestiging(
                kvk=kvk, vestiging=vestiging
            )
        except User.DoesNotExist:
            target_user = User.eherkenning_objects.create(kvk=kvk, vestiging=vestiging)

        if target_user == self._request.user:
            return  # Nothing to do

        # Persist these values before the session is cleared
        previous_id_token = self._request.session["oidc_id_token"]
        previous_backend = self._request.session["_auth_user_backend"]
        previous_initial_branch_selection_done = self.is_initial_branch_selection_done()

        # Clear the session
        django_logout(self._request)

        # Login and re-sync the previous values
        django_login(
            request=self._request,
            user=target_user,
            backend=previous_backend,
        )
        self.persist_eherkenning_state_for_user(
            user=target_user,
            is_branch_restricted=False,
            initial_branch_selection_done=previous_initial_branch_selection_done,
        )
        self._request.session["oidc_id_token"] = previous_id_token
        self._request.session.save()
