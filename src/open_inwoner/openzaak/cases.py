import logging
from typing import List, Optional

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import ZaakType
from zgw_consumers.api_models.zaken import Zaak
from zgw_consumers.service import get_paginated_results

from .clients import build_client

logger = logging.getLogger(__name__)


def fetch_cases(user_bsn: str) -> List[Zaak]:
    client = build_client("zaak")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "zaak",
            request_kwargs={
                "params": {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": user_bsn
                },
            },
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    cases = factory(Zaak, response)

    return cases


def fetch_single_case(case_uuid: str) -> Optional[Zaak]:
    client = build_client("zaak")

    if client is None:
        return

    try:
        response = client.retrieve("zaak", uuid=case_uuid)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case = factory(Zaak, response)

    return case


def fetch_case_types() -> List[ZaakType]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(client, "zaaktype")
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    case_types = factory(ZaakType, response)

    return case_types


def fetch_single_case_type(case_type_url: str) -> Optional[ZaakType]:
    client = build_client("catalogi")

    if client is None:
        return

    try:
        response = client.retrieve("zaaktype", url=case_type_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case_type = factory(ZaakType, response)

    return case_type
