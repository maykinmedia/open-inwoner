import concurrent.futures
import logging

from django.conf import settings

from zgw_consumers.concurrent import parallel

from .api_models import Zaak
from .clients import (
    CatalogiClient,
    ZakenClient,
    build_catalogi_client,
    build_zaken_client,
)
from .models import ZaakTypeConfig, ZaakTypeStatusTypeConfig
from .utils import is_zaak_visible

logger = logging.getLogger(__name__)


def resolve_zaak_type(case: Zaak, client: CatalogiClient | None = None) -> None:
    """
    Resolve `case.zaaktype` (`str`) to a `ZaakType(ZGWModel)` object

    Note: the result of `fetch_single_case_type` is cached, hence a request
          is only made for new case type urls
    """
    case_type_url = case.zaaktype
    client = client or build_catalogi_client()
    if client:
        case_type = client.fetch_single_case_type(case_type_url)
        case.zaaktype = case_type


def resolve_status(case: Zaak, client: ZakenClient | None = None) -> None:
    """
    Resolve `case.status` (`str`) to a `Status(ZGWModel)` object
    """
    client = client or build_zaken_client()
    if client:
        case.status = client.fetch_single_status(case.status)


def resolve_status_type(case: Zaak, client: CatalogiClient | None = None) -> None:
    """
    Resolve `case.status.statustype` (`str`) to a `StatusType(ZGWModel)` object
    """
    statustype_url = case.status.statustype
    client = client or build_catalogi_client()
    if client:
        case.status.statustype = client.fetch_single_status_type(statustype_url)


def resolve_resultaat(case: Zaak, client: ZakenClient | None = None) -> None:
    """
    Resolve `case.resultaat` (`str`) to a `Resultaat(ZGWModel)` object
    """
    client = client or build_zaken_client()
    if client and case.resultaat:
        case.resultaat = client.fetch_single_result(case.resultaat)


def resolve_resultaat_type(case: Zaak, client: CatalogiClient | None = None) -> None:
    """
    Resolve `case.resultaat.resultaattype` (`str`) to a `ResultaatType(ZGWModel)` object
    """
    client = client or build_catalogi_client()
    if client and case.resultaat:
        case.resultaat.resultaattype = client.fetch_single_resultaat_type(
            case.resultaat.resultaattype
        )


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
    zaken_client = build_zaken_client()
    catalogi_client = build_catalogi_client()

    def preprocess_case(case: Zaak) -> None:
        resolve_status(case, client=zaken_client)
        resolve_status_type(case, client=catalogi_client)
        resolve_resultaat(case, client=zaken_client)
        resolve_resultaat_type(case, client=catalogi_client)
        add_zaak_type_config(case)
        add_status_type_config(case)

    # TODO error handling if these are none?
    # use contextmanager to ensure the `requests.Session` is reused
    with zaken_client, catalogi_client:
        with parallel(max_workers=settings.CASE_LIST_NUM_THREADS) as executor:
            futures = [
                executor.submit(resolve_zaak_type, case, client=catalogi_client)
                for case in cases
            ]
            concurrent.futures.wait(futures)

            cases = [case for case in cases if case.status and is_zaak_visible(case)]

            futures = [executor.submit(preprocess_case, case) for case in cases]
            concurrent.futures.wait(futures)

    cases.sort(key=lambda case: case.startdatum, reverse=True)

    return cases
