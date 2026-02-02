import requests
import structlog
from ape_pie.client import APIClient
from pydantic import ValidationError

from .api_models import AfvalProfiel
from .exceptions import MijnAfvalException

logger = structlog.stdlib.get_logger(__name__)


class OpenAfvalAPIClient(APIClient):
    def get_afval_profiel(self, bsn: str) -> AfvalProfiel:
        try:
            response = self.get("afval-profiel/987654321")
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
