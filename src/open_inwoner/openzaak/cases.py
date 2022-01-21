import logging

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.zaken import Zaak

from .models import OpenZaakConfig

logger = logging.getLogger(__name__)


def fetch_cases(user):
    config = OpenZaakConfig.get_solo()

    if not config.service:
        logger.warning("no service defined for Open Zaak")
        return []

    if user.bsn is None:
        return []

    client = config.service.build_client()
    try:
        response = client.list(
            "zaak",
            request_kwargs={
                "headers": {
                    "Accept-Crs": "EPSG:4326",
                },
                "params": {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": f"{user.bsn}"
                },
            },
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    cases = [factory(Zaak, data) for data in response.get("results", [])]

    return cases
