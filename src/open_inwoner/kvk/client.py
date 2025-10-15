from functools import cached_property
from urllib.parse import urlencode

import requests
import structlog
from requests.exceptions import InvalidJSONError, JSONDecodeError

from open_inwoner.utils.decorators import cache as cache_result

from .constants import CompanyType
from .exceptions import KVKAPIException
from .models import KvKConfig

logger = structlog.stdlib.get_logger(__name__)


class KvKClient:
    def __init__(self, config: KvKConfig | None = None):
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
    def _build_url(endpoint: str, params: dict | None = None) -> str:
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

    def _request(self, endpoint: str, params: dict | None = None) -> dict | None:
        if not self.config or not self.config.api_root:
            return {}

        url = self._build_url(endpoint, params=params)
        request_kwargs = self._build_request_kwargs()

        try:
            response = requests.get(url, **request_kwargs)
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.warning("Error response while making request to KVK API")
            raise KVKAPIException.from_error_response(exc.response) from exc
        except requests.RequestException as exc:
            logger.warning("Error while making request to KVK API")
            raise KVKAPIException from exc

        try:
            data = response.json()
        except (InvalidJSONError, JSONDecodeError, ValueError) as exc:
            logger.exception("Unable to parse information from the KVK API")
            raise KVKAPIException from exc

        return data

    #
    # Interface
    #
    @cached_property
    def search_endpoint(self):
        return self._urljoin(self.config.api_root, "v2", "zoeken")

    @cached_property
    def basisprofielen_endpoint(self):
        return self._urljoin(self.config.api_root, "v1", "basisprofielen")

    @cached_property
    def vestigingsprofielen_endpoint(self):
        return self._urljoin(self.config.api_root, "v1", "vestigingsprofielen")

    def search(self, **kwargs) -> dict:
        """
        Generic call to the 'Zoeken' endpoint of the KvK API

        Customize by passing appropriate kwargs or use the more specific methods

        Cf. https://developers.kvk.nl/nl/documentation/zoeken-api
        """
        kwargs.update({"resultatenPerPagina": 100})
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

    def get_vestiging(self, vestiging: str) -> dict | None:
        vestigingen = self.search(vestigingsnummer=vestiging).get("resultaten", [])

        if not vestigingen:
            logger.info("No vestiging found", vestigingsnummer=vestiging)
            return None

        return vestigingen[0]

    def get_all_company_branches(self, kvk: str, **kwargs) -> list[dict | None]:
        """
        Get data about all branches ("hoofdvestiging" + "nevenvestigingen") of a company.

        Filter response from KvK API (remove elements which are not specific branches) and
        sort the results (move the main branch ("hoofdvestiging") to the front of the list)
        """
        kwargs.update({"kvkNummer": kvk})
        branches = self.search(**kwargs).get("resultaten", [])

        for branch in branches.copy():
            if not (
                branch["type"] == "hoofdvestiging" or branch["type"] == "nevenvestiging"
            ):
                branches.remove(branch)
            elif branch["type"] == "hoofdvestiging":
                branches.insert(0, branches.pop(branches.index(branch)))

        return branches

    @cache_result("kvk:{kvk}")
    def get_basisprofiel(self, kvk: str) -> dict:
        return self._request(f"{self.basisprofielen_endpoint}/{kvk}")

    def get_vestigingsprofiel(self, vestiging: str) -> dict:
        vestigingsprofiel = (
            self._request(f"{self.vestigingsprofielen_endpoint}/{vestiging}") or {}
        )
        return vestigingsprofiel

    def retrieve_rsin_with_kvk(
        self, kvk: str, basisprofiel: dict | None = None
    ) -> str | None:
        basisprofiel = self.get_basisprofiel(kvk=kvk)

        try:
            rsin = basisprofiel["_embedded"]["eigenaar"]["rsin"]
        except KeyError:
            rsin = None

        return rsin
