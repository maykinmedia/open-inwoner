import requests
import structlog
from ape_pie.client import APIClient
from pydantic import ValidationError

from .api_models import AfvalProfiel
from .exceptions import MijnAfvalException

logger = structlog.stdlib.get_logger(__name__)


class OpenAfvalAPIClient(APIClient):
    def get_afval_profiel(
        self,
        bsn: str,
        adressen: list[str] | None = None,
        afval_type: str | None = None,
        startdatum: str | None = None,
        einddatum: str | None = None,
    ) -> AfvalProfiel:
        """
        Fetch AfvalProfiel for a BSN with optional filters.

        Args:
            bsn: BSN of the customer
            adressen: Filter container locations by address (multiple allowed)
            afval_type: Filter containers by waste type (e.g., 'gft', 'restafval')
            startdatum: Filter ledigingen from this date (YYYY-MM-DD)
            einddatum: Filter ledigingen until this date (YYYY-MM-DD)

        Returns:
            AfvalProfiel model instance

        Raises:
            MijnAfvalException: On any API or validation error
        """
        params = {}
        if adressen:
            params["adres"] = adressen
        if afval_type:
            params["afval-type"] = afval_type
        if startdatum:
            params["startdatum"] = startdatum
        if einddatum:
            params["einddatum"] = einddatum

        try:
            response = self.get("afval-profiel/111222333/", params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code
            if status_code < 500:
                logger.exception("Client error", status_code=status_code)
            else:
                logger.exception("Server error", status_code=status_code)
            raise MijnAfvalException from exc
        except requests.exceptions.RequestException as exc:
            logger.exception("Network error when fetching Afval profiel")
            raise MijnAfvalException from exc

        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError as exc:
            logger.exception("Invalid JSON from OpenAfval API")
            raise MijnAfvalException from exc

        try:
            return AfvalProfiel.model_validate(response_json)
        except ValidationError as exc:
            logger.exception("Invalid data for AfvalProfiel")
            raise MijnAfvalException from exc
