from urllib.parse import quote

from django.conf import settings

import structlog

from open_inwoner.utils.api import BaseAPIClient
from open_inwoner.utils.decorators import cache as cache_result

from .api_models import LapostaList, Member, UserData
from .exceptions import (
    LapostaAPIClientError,
    LapostaAPIError,
    LapostaAPIInvalidJSONError,
    LapostaAPINetworkError,
    LapostaAPIServerError,
)
from .models import LapostaConfig

logger = structlog.stdlib.get_logger(__name__)


def quote_email(email: str) -> str:
    """
    The API requires + to be double encoded
    """
    email_with_quoted_plus = email.replace("+", quote("+"))
    return quote(email_with_quoted_plus)


class LapostaClient(BaseAPIClient):
    network_error_type = LapostaAPINetworkError
    client_error_type = LapostaAPIClientError
    server_error_type = LapostaAPIServerError
    invalid_json_error_type = LapostaAPIInvalidJSONError

    list_ids: list[str]

    def __init__(self, *args, list_ids: list[str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        # The lists a subscription lookup covers, from
        # `LapostaConfig.limit_list_selection_to`. Client state rather than an
        # argument so that the lookup and its invalidation agree on the cache key:
        # the subscribe/unsubscribe calls know an email address but have no reason
        # to know which lists some other caller asked about.
        self.list_ids = list_ids or []

    @property
    def _list_ids_key(self) -> str:
        """`list_ids` rendered for a cache key.

        Joined rather than interpolated as a list: the decorator `repr()`s values,
        and a list's repr contains spaces, which are not valid in a memcached key.
        """
        return ",".join(self.list_ids)

    @cache_result("laposta_lists", timeout=settings.CACHE_LAPOSTA_API_TIMEOUT)
    def get_lists(self) -> list[LapostaList]:
        response = self.get("list")
        self.raise_for_status(response)
        data = self.parse_json(response)

        if not isinstance(data, dict):
            raise LapostaAPIError(
                f"Expected dict response from Laposta list endpoint, got {type(data).__name__}"
            )
        return [LapostaList(**entry["list"]) for entry in data.get("data", [])]

    def create_subscription(self, list_id: str, user_data: UserData) -> Member | None:
        response = self.post(
            "member", json={"list_id": list_id, **user_data.model_dump()}
        )

        if response.status_code == 400:
            data = response.json()
            error = data.get("error", {})
            # Handle scenario where a subscription exists in the API, but not locally
            if error.get("code") == 204 and error.get("parameter") == "email":
                logger.info("Subscription already exists for user")
                return Member(
                    member_id=data["error"]["member_id"],
                    list_id=list_id,
                    email=user_data.email,
                    ip=user_data.ip,
                )

        self.raise_for_status(response)
        data = self.parse_json(response)

        # Ensure the current subscriptions for this email address are fetched again
        # after this API call
        self.get_subscriptions_for_email.invalidate(self, user_data.email)

        return Member(**data["member"])

    def remove_subscription(self, list_id: str, email: str) -> Member | None:
        response = self.delete(
            f"member/{quote_email(email)}", params={"list_id": list_id}
        )
        if response.status_code == 400:
            data = response.json()
            error = data.get("error", {})
            # Handle scenario where a subscription does not exists in the API,
            # but it does exist locally
            if error.get("code") == 203 and error.get("parameter") == "member_id":
                logger.info("Subscription does not exist for user")
                return None

        self.raise_for_status(response)
        data = self.parse_json(response)

        # Ensure the current subscriptions for this email address are fetched again
        # after this API call
        self.get_subscriptions_for_email.invalidate(self, email)

        return Member(**data["member"])

    @cache_result(
        "laposta_list_subscriptions:{self._list_ids_key}:{email}",
        timeout=settings.CACHE_LAPOSTA_API_TIMEOUT,
    )
    def get_subscriptions_for_email(self, email: str) -> list[str]:
        """Return which of the client's lists this email is subscribed to.

        The lists are part of the cache key, so narrowing or widening the configured
        selection cannot serve an answer collected for a different one.
        """
        subscribed_to = []
        for list_id in self.list_ids:
            response = self.get(
                f"member/{quote_email(email)}", params={"list_id": list_id}
            )
            if response.status_code == 200:
                subscribed_to.append(list_id)
        return subscribed_to


def create_laposta_client() -> LapostaClient | None:
    config = LapostaConfig.get_solo()
    if config.api_root:
        return LapostaClient.configure_from(
            config, list_ids=config.limit_list_selection_to
        )
