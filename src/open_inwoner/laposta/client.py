import logging
from typing import Optional

from django.conf import settings

from ape_pie.client import APIClient
from requests.exceptions import RequestException

from open_inwoner.utils.api import ClientError, get_json_response

from ..utils.decorators import cache as cache_result
from .api_models import LapostaList, Member, UserData
from .models import LapostaConfig

logger = logging.getLogger(__name__)


class LapostaClient(APIClient):
    @cache_result("laposta_lists", timeout=settings.CACHE_LAPOSTA_API_TIMEOUT)
    def get_lists(self) -> list[LapostaList]:
        try:
            response = self.get("list")
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        if not data:
            return []

        lists = [LapostaList(**entry["list"]) for entry in data["data"]]

        return lists

    def create_subscription(self, list_id: str, user_data: UserData) -> Member | None:
        response = self.post("member", data={"list_id": list_id, **user_data.dict()})

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

        data = get_json_response(response)
        if not data:
            return None

        return Member(**data["member"])

    def remove_subscription(self, list_id: str, member_id: str) -> Member | None:
        response = self.delete(f"member/{member_id}", params={"list_id": list_id})

        if response.status_code == 400:
            data = response.json()
            error = data.get("error", {})
            # Handle scenario where a subscription does not exists in the API,
            # but it does exist locally
            if error.get("code") == 203 and error.get("parameter") == "member_id":
                logger.info("Subscription does not exist for user")
                return None

        data = get_json_response(response)
        if not data:
            return None

        return Member(**data["member"])


def create_laposta_client() -> Optional[LapostaClient]:
    config = LapostaConfig.get_solo()
    if config.api_root:
        return LapostaClient.configure_from(config)
