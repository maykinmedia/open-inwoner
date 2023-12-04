import copy
import logging
from typing import List, Optional

from django.conf import settings

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes
from zgw_consumers.service import get_paginated_results

from ..utils.decorators import cache as cache_result
from .api_models import Resultaat, Rol, Status, Zaak, ZaakInformatieObject
from .catalog import fetch_single_case_type, fetch_single_status_type
from .clients import build_client
from .models import OpenZaakConfig, ZaakTypeConfig, ZaakTypeStatusTypeConfig
from .utils import is_zaak_visible

logger = logging.getLogger(__name__)


@cache_result(
    "cases:{user_bsn}:{max_cases}:{identificatie}",
    timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
)
def fetch_cases(
    user_bsn: str, max_cases: Optional[int] = 100, identificatie: Optional[str] = None
) -> List[Zaak]:
    """
    retrieve cases for particular user with allowed confidentiality level

    :param:max_cases - used to limit the number of requests to list_zaken resource. The default
    value = 100, which means only one 1 request
    :param:identificatie - used to filter the cases by a specific identification
    """
    client = build_client("zaak")

    if client is None:
        return []

    config = OpenZaakConfig.get_solo()

    params = {
        "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": user_bsn,
        "maximaleVertrouwelijkheidaanduiding": config.zaak_max_confidentiality,
    }
    if identificatie:
        params.update({"identificatie": identificatie})

    try:
        response = get_paginated_results(
            client,
            "zaak",
            minimum=max_cases,
            request_kwargs={
                "params": params,
            },
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    cases = factory(Zaak, response)

    return cases


@cache_result(
    "cases:{kvk_or_rsin}:{max_cases}:{zaak_identificatie}",
    timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
)
def fetch_cases_by_kvk_or_rsin(
    kvk_or_rsin: Optional[str],
    max_cases: Optional[int] = 100,
    zaak_identificatie: Optional[str] = None,
) -> List[Zaak]:
    """
    retrieve cases for particular company with allowed confidentiality level

    :param max_cases: - used to limit the number of requests to list_zaken resource. The default
    value = 100, which means only one 1 request
    :param zaak_identificatie: - used to filter the cases by a unique Zaak identification number
    """
    if not kvk_or_rsin:
        return []

    client = build_client("zaak")

    if client is None:
        return []

    config = OpenZaakConfig.get_solo()

    params = {
        "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId": kvk_or_rsin,
        "maximaleVertrouwelijkheidaanduiding": config.zaak_max_confidentiality,
    }
    if zaak_identificatie:
        params.update({"identificatie": zaak_identificatie})

    try:
        response = get_paginated_results(
            client,
            "zaak",
            minimum=max_cases,
            request_kwargs={
                "params": params,
            },
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    cases = factory(Zaak, response)

    return cases


@cache_result("single_case:{case_uuid}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_single_case(case_uuid: str) -> Optional[Zaak]:
    client = build_client("zaak")

    if client is None:
        return

    try:
        response = client.retrieve("zaak", uuid=case_uuid)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case = factory(Zaak, response)

    return case


@cache_result(
    "single_case_information_object:{url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT
)
def fetch_single_case_information_object(url: str) -> Optional[ZaakInformatieObject]:
    client = build_client("zaak")

    if client is None:
        return

    try:
        response = client.retrieve("zaakinformatieobject", url=url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case = factory(ZaakInformatieObject, response)

    return case


def fetch_case_by_url_no_cache(case_url: str) -> Optional[Zaak]:
    client = build_client("zaak")
    try:
        response = client.retrieve("zaak", url=case_url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case = factory(Zaak, response)

    return case


# not cached for quicker uploaded document visibility
def fetch_case_information_objects(case_url: str) -> List[ZaakInformatieObject]:
    client = build_client("zaak")

    if client is None:
        return []

    try:
        response = client.list(
            "zaakinformatieobject",
            request_kwargs={
                "params": {"zaak": case_url},
            },
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    case_info_objects = factory(ZaakInformatieObject, response)

    return case_info_objects


@cache_result("status_history:{case_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_status_history(case_url: str) -> List[Status]:
    return fetch_status_history_no_cache(case_url)


def fetch_status_history_no_cache(case_url: str) -> List[Status]:
    client = build_client("zaak")

    if client is None:
        return []

    try:
        response = client.list("status", request_kwargs={"params": {"zaak": case_url}})
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    statuses = factory(Status, response["results"])

    return statuses


@cache_result("status:{status_url}", timeout=60 * 60)
def fetch_single_status(status_url: str) -> Optional[Status]:
    client = build_client("zaak")

    if client is None:
        return

    try:
        response = client.retrieve("status", url=status_url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    status = factory(Status, response)

    return status


@cache_result(
    "case_roles:{case_url}:{role_desc_generic}",
    timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
)
def fetch_case_roles(
    case_url: str, role_desc_generic: Optional[str] = None
) -> List[Rol]:
    client = build_client("zaak")

    if client is None:
        return []

    params = {
        "zaak": case_url,
    }
    if role_desc_generic:
        assert role_desc_generic in RolOmschrijving.values
        params["omschrijvingGeneriek"] = role_desc_generic

    try:
        response = get_paginated_results(
            client,
            "rol",
            request_kwargs={"params": params},
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    roles = factory(Rol, response)

    # Taiga #961 process eSuite response to apply ignored filter query
    if role_desc_generic:
        roles = [r for r in roles if r.omschrijving_generiek == role_desc_generic]

    return roles


# implicitly cached because it uses fetch_case_roles()
def fetch_roles_for_case_and_bsn(case_url: str, bsn: str) -> List[Rol]:
    """
    note we do a query on all case_roles and then manually filter our roles from the result,
    because e-Suite doesn't support querying on both "zaak" AND "betrokkeneIdentificatie__natuurlijkPersoon__inpBsn"

    see Taiga #948
    """
    case_roles = fetch_case_roles(case_url)
    if not case_roles:
        return []

    bsn_roles = []
    for role in case_roles:
        if role.betrokkene_type == RolTypes.natuurlijk_persoon:
            inp_bsn = role.betrokkene_identificatie.get("inp_bsn")
            if inp_bsn and inp_bsn == bsn:
                bsn_roles.append(role)

    return bsn_roles


# implicitly cached because it uses fetch_case_roles()
def fetch_roles_for_case_and_kvk(case_url: str, kvk_or_rsin: str) -> List[Rol]:
    """
    note we do a query on all case_roles and then manually filter our roles from the result,
    because e-Suite doesn't support querying on both "zaak" AND "betrokkeneIdentificatie__nietNatuurlijkPersoon__inn_nnp_id"

    see Taiga #948
    """
    case_roles = fetch_case_roles(case_url)
    if not case_roles:
        return []

    roles = []
    for role in case_roles:
        if role.betrokkene_type == RolTypes.niet_natuurlijk_persoon:
            nnp_id = role.betrokkene_identificatie.get("inn_nnp_id")
            if nnp_id and nnp_id == kvk_or_rsin:
                roles.append(role)

    return roles


# not cached because currently only used in info-object download view
def fetch_case_information_objects_for_case_and_info(
    case_url: str, info_object_url: str
) -> List[ZaakInformatieObject]:
    client = build_client("zaak")

    if client is None:
        return []

    try:
        response = client.list(
            "zaakinformatieobject",
            request_kwargs={
                "params": {
                    "zaak": case_url,
                    "informatieobject": info_object_url,
                },
            },
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    case_info_objects = factory(ZaakInformatieObject, response)

    return case_info_objects


@cache_result("single_result:{result_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_single_result(result_url: str) -> Optional[Resultaat]:
    client = build_client("zaak")

    if client is None:
        return

    try:
        response = client.retrieve("result", url=result_url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    result = factory(Resultaat, response)

    return result


def connect_case_with_document(case_url: str, document_url: str) -> Optional[dict]:
    client = build_client("zaak")

    if client is None:
        return

    try:
        response = client.create(
            "zaakinformatieobject", {"zaak": case_url, "informatieobject": document_url}
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    return response


def resolve_zaak_type(case: Zaak) -> None:
    """
    Resolve `case.zaaktype` (`str`) to a `ZaakType(ZGWModel)` object

    Note: the result of `fetch_single_case_type` is cached, hence a request
          is only made for new case type urls
    """
    case_type_url = case.zaaktype
    case_type = fetch_single_case_type(case_type_url)
    case.zaaktype = case_type


def resolve_status(case: Zaak) -> None:
    """
    Resolve `case.status` (`str`) to a `Status(ZGWModel)` object
    """
    case.status = fetch_single_status(case.status)


def resolve_status_type(case: Zaak) -> None:
    """
    Resolve `case.statustype` (`str`) to a `StatusType(ZGWModel)` object
    """
    statustype_url = case.status.statustype
    case.status.statustype = fetch_single_status_type(statustype_url)


def add_zaak_type_config(case: Zaak) -> None:
    """
    Add `ZaakTypeConfig` corresponding to the zaaktype type url of the case

    Note: must be called after `resolve_zaak_type` since we're using the `uuid` and
        `identificatie` from `case.zaaktype`
    """
    try:
        case.zaaktype_config = ZaakTypeConfig.objects.filter_case_type(
            case.zaaktype
        ).get()
    except ZaakTypeConfig.DoesNotExist:
        pass


def add_status_type_config(case: Zaak) -> None:
    """
    Add `ZaakTypeStatusTypeConfig` corresponding to the status type url of the case

    Note: must be called after `resolve_status_type` since we're getting the
          status type url from `case.status.statustype`
    """
    try:
        case.statustype_config = ZaakTypeStatusTypeConfig.objects.get(
            zaaktype_config=case.zaaktype_config,
            statustype_url=case.status.statustype.url,
        )
    except (AttributeError, ZaakTypeStatusTypeConfig.DoesNotExist):
        pass


def preprocess_data(cases: list[Zaak]) -> list[Zaak]:
    """
    Resolve zaaktype and statustype, add status type config, filter for visibility

    Note: we need to iterate twice over `cases` because the `zaak_type` must be
          resolved to a `ZaakType` object before we can filter by visibility
    """
    for case in cases:
        resolve_zaak_type(case)

    cases = [case for case in cases if case.status and is_zaak_visible(case)]

    for case in cases:
        resolve_status(case)
        resolve_status_type(case)
        add_zaak_type_config(case)
        add_status_type_config(case)

    cases.sort(key=lambda case: case.startdatum, reverse=True)

    return cases
