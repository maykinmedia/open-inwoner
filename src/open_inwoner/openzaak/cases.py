import logging
from typing import List, Optional

from django.conf import settings

from zgw_consumers.api_models.constants import RolTypes

from ..utils.decorators import cache as cache_result
from .api_models import Resultaat, Rol, Status, Zaak, ZaakInformatieObject
from .catalog import fetch_single_case_type, fetch_single_status_type
from .clients import build_client
from .models import ZaakTypeConfig, ZaakTypeStatusTypeConfig
from .utils import is_zaak_visible

logger = logging.getLogger(__name__)
CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


def fetch_cases(
    user_bsn: str, max_requests: Optional[int] = 1, identificatie: Optional[str] = None
) -> List[Zaak]:
    """
    retrieve cases for particular user with allowed confidentiality level

    :param:max_requests - used to limit the number of requests to list_zaken resource.
    :param:identificatie - used to filter the cases by a specific identification
    """
    client = build_client("zaak")

    if client is None:
        return []

    return client.fetch_cases(
        user_bsn=user_bsn, max_requests=max_requests, identificatie=identificatie
    )


def fetch_cases_by_kvk_or_rsin(
    kvk_or_rsin: Optional[str],
    max_requests: Optional[int] = 1,
    zaak_identificatie: Optional[str] = None,
    vestigingsnummer: Optional[str] = None,
) -> List[Zaak]:
    """
    retrieve cases for particular company with allowed confidentiality level

    :param max_requests: - used to limit the number of requests to list_zaken resource.
    :param zaak_identificatie: - used to filter the cases by a unique Zaak identification number
    :param vestigingsnummer: - used to filter the cases by a vestigingsnummer
    """
    client = build_client("zaak")

    if client is None:
        return []

    return client.fetch_cases_by_kvk_or_rsin(
        kvk_or_rsin=kvk_or_rsin,
        max_requests=max_requests,
        zaak_identificatie=zaak_identificatie,
        vestigingsnummer=vestigingsnummer,
    )


def fetch_single_case(case_uuid: str) -> Optional[Zaak]:
    client = build_client("zaak")

    if client is None:
        return

    return client.fetch_single_case(case_uuid)


def fetch_single_case_information_object(url: str) -> Optional[ZaakInformatieObject]:
    client = build_client("zaak")

    if client is None:
        return

    return client.fetch_single_case_information_object(url)


def fetch_case_by_url_no_cache(case_url: str) -> Optional[Zaak]:
    client = build_client("zaak")
    return client.fetch_case_by_url_no_cache(case_url)


# not cached for quicker uploaded document visibility
def fetch_case_information_objects(case_url: str) -> List[ZaakInformatieObject]:
    client = build_client("zaak")

    if client is None:
        return []

    return client.fetch_case_information_objects(case_url)


@cache_result("status_history:{case_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_status_history(case_url: str) -> List[Status]:
    return fetch_status_history_no_cache(case_url)


def fetch_status_history_no_cache(case_url: str) -> List[Status]:
    client = build_client("zaak")

    if client is None:
        return []

    return client.fetch_status_history_no_cache(case_url)


def fetch_single_status(status_url: str) -> Optional[Status]:
    client = build_client("zaak")

    if client is None:
        return

    return client.fetch_single_status(status_url)


def fetch_case_roles(
    case_url: str, role_desc_generic: Optional[str] = None
) -> List[Rol]:
    client = build_client("zaak")

    if client is None:
        return []

    return client.fetch_case_roles(case_url, role_desc_generic=role_desc_generic)


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
def fetch_roles_for_case_and_kvk_or_rsin(case_url: str, kvk_or_rsin: str) -> List[Rol]:
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


def fetch_roles_for_case_and_vestigingsnummer(
    case_url: str, vestigingsnummer: str
) -> List[Rol]:
    """
    note we do a query on all case_roles and then manually filter our roles from the result,
    because e-Suite doesn't support querying on both "zaak" AND "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer"

    see Taiga #948
    """
    case_roles = fetch_case_roles(case_url)
    if not case_roles:
        return []

    roles = []
    for role in case_roles:
        if role.betrokkene_type == RolTypes.vestiging:
            identifier = role.betrokkene_identificatie.get("vestigings_nummer")
            if identifier and identifier == vestigingsnummer:
                roles.append(role)

    return roles


# not cached because currently only used in info-object download view
def fetch_case_information_objects_for_case_and_info(
    case_url: str, info_object_url: str
) -> List[ZaakInformatieObject]:
    client = build_client("zaak")

    if client is None:
        return []

    return client.fetch_case_information_objects_for_case_and_info(
        case_url, info_object_url
    )


def fetch_single_result(result_url: str) -> Optional[Resultaat]:
    client = build_client("zaak")

    if client is None:
        return

    return client.fetch_single_result(result_url)


def connect_case_with_document(case_url: str, document_url: str) -> Optional[dict]:
    client = build_client("zaak")

    if client is None:
        return

    return client.connect_case_with_document(case_url, document_url)


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
