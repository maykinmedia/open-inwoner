import logging

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.zaken import Zaak
from zgw_consumers.service import get_paginated_results

from .clients import build_client

logger = logging.getLogger(__name__)


def fetch_cases(user):
    client = build_client("zaak")

    if client is None or user.bsn is None:
        return []

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


def fetch_specific_case(user, case_uuid):
    client = build_client("zaak")

    if client is None or user.bsn is None:
        return

    try:
        response = client.retrieve("zaak", uuid=case_uuid)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return
    case = factory(Zaak, response)

    return case
