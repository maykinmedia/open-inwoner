import logging
from typing import Optional
from urllib.parse import urlencode, urljoin

import requests
from simplejson.errors import JSONDecodeError

from .models import KvKConfig

logger = logging.getLogger(__name__)


class KvKClient:
    def __init__(self, config: KvKConfig = None):
        self.config = config or KvKConfig.get_solo()
        self.search_endpoint = urljoin(self.config.api_root, "zoeken")

    @staticmethod
    def _build_url(endpoint: str, params: Optional[dict] = None) -> str:
        if not params:
            return endpoint

        encoded_params = urlencode(params, doseq=True)
        return f"{endpoint}?{encoded_params}"

    def _build_request_kwargs(self) -> dict:
        request_kwargs = {
            "headers": {
                "apikey": self.config.api_key,
            },
            "verify": self.config.verify,
            "cert": self.config.cert,
        }

        return request_kwargs

    def _request(self, endpoint: str, params: dict) -> dict:
        if not self.config or not self.config.api_root:
            return {}

        url = self._build_url(endpoint, params=params)
        request_kwargs = self._build_request_kwargs()

        try:
            response = requests.get(url, **request_kwargs)
        except requests.RequestException as ex:
            logger.exception("Unable to retrieve information from the KVK API: %s", ex)
            return {}

        try:
            data = response.json()
        except (AttributeError, JSONDecodeError, requests.RequestException) as ex:
            logger.exception("Unable to parse information from the KVK API: %s", ex)
            return {}

        return data

    def search(self, kvk: str, **kwargs) -> dict:
        params = {"kvkNummer": kvk, **kwargs}

        companies = self._request(self.search_endpoint, params=params).get(
            "resultaten", []
        )

        if not companies:
            return {}

        return companies[0]

    def retrieve_rsin_with_kvk(self, kvk, **kwargs) -> Optional[str]:
        company_data = self.search(kvk)

        if not company_data:
            return None

        basisprofiel_link = None
        for link in company_data["links"]:
            if link["rel"] == "basisprofiel":
                basisprofiel_link = link["href"]
                break

        basisprofiel = self._request(basisprofiel_link, {})
        try:
            rsin = basisprofiel["_embedded"]["eigenaar"]["rsin"]
        except KeyError:
            rsin = None

        return rsin
