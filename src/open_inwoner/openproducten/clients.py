import logging

from django.core.files import File as DjangoFile
from django.core.files.temp import NamedTemporaryFile

import requests
from ape_pie.client import APIClient
from filer.models.filemodels import File
from filer.models.imagemodels import Image
from requests import RequestException
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import build_client

from open_inwoner.utils.api import ClientError, get_json_response

from .api_models import Category, ProductType
from .models import OpenProductenConfig

logger = logging.getLogger(__name__)


class OpenProductenClient(APIClient):
    def fetch_producttypes_no_cache(self) -> list[ProductType]:
        try:
            response = self.get("producttypes/")
            data: list = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        product_types = factory(ProductType, data)

        return product_types

    def fetch_categories_no_cache(self) -> list[Category]:
        try:
            response = self.get("categories/")
            data: list = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        categories = factory(Category, data)

        return categories

    def _fetch_file(self, url) -> DjangoFile | None:
        try:
            # APIClient checks if base url is the same
            response = requests.get(url)

            temp_file = NamedTemporaryFile(delete=True)
            temp_file.write(response.content)

            return DjangoFile(temp_file)

        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return None

    def get_image(self, url) -> Image | None:

        if not url:
            return None

        file = self._fetch_file(url)

        if not file:
            return None

        return Image.objects.create(original_filename=url.split("/")[-1], file=file)

    def get_file(self, url) -> File | None:
        if not url:
            return None

        file = self._fetch_file(url)

        if not file:
            return None

        return File.objects.create(original_filename=url.split("/")[-1], file=file)


def build_open_producten_client():
    config = OpenProductenConfig.get_solo()
    if not config.producten_service:
        raise ValueError("No producten service configured")
    return build_client(config.producten_service, client_factory=OpenProductenClient)
