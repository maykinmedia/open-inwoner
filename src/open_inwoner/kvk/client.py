import logging
from functools import cached_property
from typing import Optional
from urllib.parse import urlencode

import requests
from simplejson.errors import JSONDecodeError

from .constants import CompanyType
from .models import KvKConfig

logger = logging.getLogger(__name__)


class KvKClient:
    def __init__(self, config: Optional[KvKConfig] = None):
        self.config = config or KvKConfig.get_solo()

    #
    # Implementation details
    #
    @staticmethod
    def _urljoin(*args) -> str:
        """
        Join parts of a url irrespective of trailing '/'
        """
        return "/".join(arg.strip("/") for arg in args)

    @staticmethod
    def _build_url(endpoint: str, params: Optional[dict] = None) -> str:
        if not params:
            return endpoint

        encoded_params = urlencode(params, doseq=True)

        return f"{endpoint}?{encoded_params}"

    def _build_request_kwargs(self) -> dict:
        request_kwargs = {"headers": {"apikey": self.config.api_key}}

        if self.config.verify:
            request_kwargs.update(verify=self.config.verify)

        if self.config.cert:
            request_kwargs.update(cert=self.config.cert)

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

    #
    # Interface: search
    #
    @cached_property
    def search_endpoint(self):
        return self._urljoin(self.config.api_root, "zoeken")

    def search(self, **kwargs) -> dict:
        """
        Generic call to the 'Zoeken' endpoint of the KvK API

        Customize by passing appropriate kwargs or use the more specific methods

        Cf. https://developers.kvk.nl/nl/documentation/zoeken-api
        """
        return self._request(self.search_endpoint, params=kwargs)

    def get_company_headquarters(self, kvk: str, **kwargs) -> dict:
        """
        Get data about the headquarters ("hoofdvestiging") of a company
        """
        kwargs.update(
            {"kvkNummer": kvk, "type": CompanyType.hoofdvestiging},
        )

        headquarters = self.search(**kwargs).get("resultaten", [])

        if not headquarters:
            return {}

        return headquarters[0]

    def get_all_company_branches(self, kvk: str, **kwargs) -> list[Optional[dict]]:
        """
        Get data about all branches ("hoofdvestiging" + "nevenvestigingen") of a company
        """
        kwargs.update({"kvkNummer": kvk})
        return self.search(**kwargs).get("resultaten", [])

    def retrieve_rsin_with_kvk(self, kvk, **kwargs) -> Optional[str]:
        company_data = self.get_company_headquarters(kvk, **kwargs)

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
