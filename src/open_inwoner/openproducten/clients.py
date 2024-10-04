import logging

from django.core.files import File as DjangoFile
from django.core.files.temp import NamedTemporaryFile

import requests
from ape_pie.client import APIClient
from requests import RequestException
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import build_client
from zgw_consumers.service import pagination_helper

from open_inwoner.utils.api import ClientError, get_json_response

from .api_models import Category, ProductType
from .models import OpenProductenConfig

logger = logging.getLogger(__name__)


class OpenProductenClient(APIClient):
    def fetch_producttypes_no_cache(self) -> list[ProductType]:
        try:
            response = self.get("producttypes/")
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        product_types = factory(ProductType, all_data)

        return product_types

    def fetch_categories_no_cache(self) -> list[Category]:
        try:
            response = self.get("categories/")
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        categories = factory(Category, all_data)

        return categories

    def fetch_file(self, url) -> DjangoFile | None:
        try:
            # APIClient checks if base url is the same
            response = requests.get(url)

            temp_file = NamedTemporaryFile(delete=True)
            temp_file.write(response.content)

            return DjangoFile(temp_file)

        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return None


def build_open_producten_client():
    config = OpenProductenConfig.get_solo()
    if not config.producten_service:
        raise ValueError("No producten service configured")
    return build_client(config.producten_service, client_factory=OpenProductenClient)
