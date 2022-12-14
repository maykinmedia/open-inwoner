import logging
from typing import List, Optional

from django.conf import settings

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes
from zgw_consumers.service import get_paginated_results

from .api_models import Resultaat, Rol, Status, Zaak, ZaakInformatieObject
from .baseclient import BaseClient
from .models import OpenZaakConfig
from .utils import cache as cache_result

logger = logging.getLogger(__name__)


@cache_result("cases:{user_bsn}:{max_cases}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_cases(
    client: BaseClient, user_bsn: str, max_cases: Optional[int] = 100
) -> List[Zaak]:
    """
    retrieve cases for particular user with allowed confidentiality level

    :param:max_cases - used to limit the number of requests to list_zaken resource. The default
    value = 100, which means only one 1 request
    """
    if not client.service:
        return []

    config = OpenZaakConfig.get_solo()

    try:
        response = get_paginated_results(
            client.api,
            "zaak",
            minimum=max_cases,
            request_kwargs={
                "params": {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": user_bsn,
                    "maximaleVertrouwelijkheidaanduiding": config.zaak_max_confidentiality,
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


@cache_result("single_case:{case_uuid}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_single_case(client: BaseClient, case_uuid: str) -> Optional[Zaak]:
    if not client.service:
        return

    try:
        response = client.api.retrieve("zaak", uuid=case_uuid)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case = factory(Zaak, response)

    return case


@cache_result("case_io_objects:{case_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_case_information_objects(
    client: BaseClient, case_url: str
) -> List[ZaakInformatieObject]:
    if not client.service:
        return []

    try:
        response = client.api.list(
            "zaakinformatieobject",
            request_kwargs={
                "params": {"zaak": case_url},
            },
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    case_info_objects = factory(ZaakInformatieObject, response)

    return case_info_objects


@cache_result("status_history:{case_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_status_history(client: BaseClient, case_url: str) -> List[Status]:
    if not client.service:
        return []

    try:
        response = client.api.list(
            "status", request_kwargs={"params": {"zaak": case_url}}
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    statuses = factory(Status, response["results"])

    return statuses


@cache_result("status:{status_url}", timeout=60 * 60)
def fetch_specific_status(client: BaseClient, status_url: str) -> Optional[Status]:
    if not client.service:
        return

    try:
        response = client.api.retrieve("status", url=status_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    status = factory(Status, response)

    return status


@cache_result(
    "case_roles:{case_url}:{role_desc_generic}",
    timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
)
def fetch_case_roles(
    client: BaseClient, case_url: str, role_desc_generic: Optional[str] = None
) -> List[Rol]:
    if not client.service:
        return []

    params = {
        "zaak": case_url,
    }
    if role_desc_generic:
        assert role_desc_generic in RolOmschrijving.values
        params["omschrijvingGeneriek"] = role_desc_generic

    try:
        response = get_paginated_results(
            client.api,
            "rol",
            request_kwargs={"params": params},
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    roles = factory(Rol, response)

    # Taiga #961 process eSuite response to apply ignored filter query
    if role_desc_generic:
        roles = [r for r in roles if r.omschrijving_generiek == role_desc_generic]

    return roles


# implicitly cached because it uses fetch_case_roles()
def fetch_roles_for_case_and_bsn(
    client: BaseClient, case_url: str, bsn: str
) -> List[Rol]:
    """
    note we do a query on all case_roles and then manually filter our roles from the result,
    because e-Suite doesn't support querying on both "zaak" AND "betrokkeneIdentificatie__natuurlijkPersoon__inpBsn"

    see Taiga #948
    """
    if not client.service:
        return []

    case_roles = fetch_case_roles(client, case_url)
    if not case_roles:
        return []

    bsn_roles = []
    for role in case_roles:
        if role.betrokkene_type == RolTypes.natuurlijk_persoon:
            inp_bsn = role.betrokkene_identificatie.get("inp_bsn")
            if inp_bsn and inp_bsn == bsn:
                bsn_roles.append(role)

    return bsn_roles


# not cached because currently only used in info-object download view
def fetch_case_information_objects_for_case_and_info(
    client: BaseClient, case_url: str, info_object_url: str
) -> List[ZaakInformatieObject]:
    if not client.service:
        return []

    try:
        response = client.api.list(
            "zaakinformatieobject",
            request_kwargs={
                "params": {
                    "zaak": case_url,
                    "informatieobject": info_object_url,
                },
            },
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    case_info_objects = factory(ZaakInformatieObject, response)

    return case_info_objects


@cache_result("single_result:{result_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_single_result(client: BaseClient, result_url: str) -> Optional[Resultaat]:
    if not client.service:
        return

    try:
        response = client.api.retrieve("result", url=result_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    result = factory(Resultaat, response)

    return result
