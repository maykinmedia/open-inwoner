import logging

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.zaken import Zaak
from zgw_consumers.service import get_paginated_results

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

    # Retrieve the list of cases (results field from the API)
    try:
        response = get_paginated_results(
            client,
            "zaak",
            request_kwargs={
                "params": {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": f"{user.bsn}"
                },
            },
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    cases = factory(Zaak, response)

    return cases
