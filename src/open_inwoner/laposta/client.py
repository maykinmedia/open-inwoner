import logging
from typing import Optional

from django.conf import settings

from ape_pie.client import APIClient
from requests.exceptions import RequestException

from open_inwoner.utils.api import get_json_response

from ..utils.decorators import cache as cache_result
from .api_models import LapostaList, UserData
from .models import LapostaConfig

logger = logging.getLogger(__name__)


class LapostaClient(APIClient):
    @cache_result("laposta_lists", timeout=settings.CACHE_LAPOSTA_API_TIMEOUT)
    def get_lists(self) -> list[LapostaList]:
        try:
            response = self.get("list")
            data = get_json_response(response)
        except (RequestException) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        if not data:
            return []

        lists = [LapostaList(**entry["list"]) for entry in data["data"]]

        return lists

    def create_subscription(
        self, list_id: str, user_data: UserData
    ) -> LapostaList | None:
        try:
            response = self.post(
                "member", data={"list_id": list_id, **user_data.dict()}
            )
            data = get_json_response(response)
        except (RequestException) as e:
            logger.exception("exception while making request", exc_info=e)
            return None

        if not data:
            return None

        return LapostaList(**data["list"])


def create_laposta_client() -> Optional[LapostaClient]:
    config = LapostaConfig.get_solo()
    if config.api_root:
        return LapostaClient.configure_from(config)
