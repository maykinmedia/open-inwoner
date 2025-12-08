import concurrent.futures
import enum
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, TypedDict, cast

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

import structlog
from zgw_consumers.concurrent import parallel

from open_inwoner.openzaak.api_models import Formulier, Zaak
from open_inwoner.openzaak.clients import (
    CatalogiClient,
    ZakenClient,
    build_zgw_client_from_service,
)
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.models import (
    ZaakTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
)
from open_inwoner.openzaak.utils import get_user_fetch_parameters, is_zaak_visible

logger = structlog.stdlib.get_logger(__name__)


class ResolveCaseException(Exception):
    """Exception indicating we were unable to resolve a cases type/status/result."""

    pass


class CaseFilterFormOption(enum.Enum):
    FORMULIER = _("Openstaande formulieren")
    ZAAK_OPEN = _("Lopende aanvragen")
    ZAAK_AFGEROND = _("Afgeronde aanvragen")


@dataclass(frozen=True)
class ZaakWithApiGroup:
    zaak: Zaak
    api_group: ZGWApiGroupConfig
    type_aanvraag: TypeAanvraag

    @property
    def identification(self) -> str:
        return self.zaak.url

    def process_data(self) -> dict:
        return {
            **self.zaak.process_data(),
            "api_group": self.api_group,
            "type_aanvraag": self.type_aanvraag.value,
        }

    def __hash__(self):
        return hash((self.identification, self.api_group.pk))


@dataclass(frozen=True)
class FormulierWithApiGroup:
    formulier: Formulier
    api_group: ZGWApiGroupConfig
    type_aanvraag: TypeAanvraag

    @property
    def identification(self) -> str:
        return self.formulier.url

    def process_data(self) -> dict:
        return {
            **self.formulier.process_data(),
            "api_group": self.api_group,
            "type_aanvraag": self.type_aanvraag.value,
        }

    def __hash__(self):
        return hash((self.identification, self.api_group.pk))


class Timeouts(TypedDict):
    fetch_raw_cases: int | float
    resolve_cases: int | float
    fetch_submissions: int | float


class CaseListService:
    request: HttpRequest
    _max_workers: int
    _timeouts: Timeouts

    def __init__(self, request: HttpRequest):
        self.request = request
        self._timeouts = {
            "fetch_raw_cases": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.3,
            "resolve_cases": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.5,
            "fetch_submissions": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.2,
        }
        self._max_workers = settings.ZGW_CASE_LIST_NUM_WORKERS

        logger.debug(
            "Configured CaseListService",
            timeouts=self._timeouts,
            max_workers=self._max_workers,
        )

        # Our resolver functions modify the case list in-place, the lock is used to
        # ensure there are no concurrent writes
        self._zaak_update_lock = threading.RLock()

    @staticmethod
    def _zaken_client_factory(group: ZGWApiGroupConfig):
        return cast(
            ZakenClient,
            build_zgw_client_from_service(
                group.zrc_service,
                use_openzaak_120_params=group.fetch_eherkenning_zaken_with_openzaak_120_params,
            ),
        )

    @staticmethod
    def _catalogi_client_factory(group: ZGWApiGroupConfig):
        return cast(CatalogiClient, build_zgw_client_from_service(group.ztc_service))

    def _get_submissions_for_api_group(
        self, group: ZGWApiGroupConfig
    ) -> list[FormulierWithApiGroup]:
        if not group.forms_client:
            raise ValueError(f"{group} has no `forms_client`")

        return [
            FormulierWithApiGroup(
                submission=sub, api_group=group, type_aanvraag=TypeAanvraag.FORMULIER
            )
            for sub in group.forms_client.fetch_open_submissions(
                **get_user_fetch_parameters(
                    self.request, use_rsin=group.fetch_eherkenning_zaken_with_rsin
                )
            )
        ]

    def get_submissions(self) -> list[FormulierWithApiGroup]:
        all_api_groups = list(
            ZGWApiGroupConfig.objects.filter(form_service__isnull=False).select_related(
                "form_service",
            )
        )

        subs_with_api_group: list[FormulierWithApiGroup] = []
        with parallel(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(self._get_submissions_for_api_group, group)
                for group in all_api_groups
            ]

        try:
            for task in concurrent.futures.as_completed(
                futures,
                timeout=self._timeouts["fetch_submissions"],
            ):
                try:
                    subs_with_api_group.extend(task.result())
                except BaseException:
                    logger.exception("Error fetching and pre-processing cases")
        except concurrent.futures.TimeoutError:
            logger.warning("Timeout while fetching submissions")

        # Sort submissions by date modified
        subs_with_api_group.sort(
            key=lambda sub: sub.formulier.datum_laatste_wijziging, reverse=True
        )

        return subs_with_api_group

    @staticmethod
    def get_case_filter_status(zaak: Zaak) -> CaseFilterFormOption:
        if zaak.einddatum:
            return CaseFilterFormOption.ZAAK_AFGEROND

        return CaseFilterFormOption.ZAAK_OPEN

    def get_case_status_frequencies(
        self,
        cases: Iterable[ZaakWithApiGroup],
        submissions: Iterable[FormulierWithApiGroup],
    ) -> dict[CaseFilterFormOption, int]:
        case_statuses = [self.get_case_filter_status(case.zaak) for case in cases]

        # add static text for open submissions
        case_statuses += [CaseFilterFormOption.FORMULIER for _ in submissions]

        return {
            status: case_statuses.count(status) for status in list(CaseFilterFormOption)
        }

    def _get_raw_cases_for_api_group(
        self, group: ZGWApiGroupConfig
    ) -> list[ZaakWithApiGroup]:
        raw_cases = group.zaken_client.fetch_cases(
            **get_user_fetch_parameters(
                self.request, use_rsin=group.fetch_eherkenning_zaken_with_rsin
            )
        )

        return [
            ZaakWithApiGroup(
                zaak=raw_cases, api_group=group, type_aanvraag=TypeAanvraag.ZAAK
            )
            for raw_cases in raw_cases
        ]

    def get_cases(self) -> list[ZaakWithApiGroup]:
        all_api_groups = list(
            ZGWApiGroupConfig.objects.select_related(
                "zrc_service",
                "ztc_service",
                "drc_service",
                "form_service",
            ).all()
        )

        # Get the raw cases for all groups
        fetched_cases: list[ZaakWithApiGroup] = []
        fetch_raw_cases_futures: list[
            concurrent.futures.Future[list[ZaakWithApiGroup]]
        ] = []
        with parallel(max_workers=self._max_workers) as executor:
            fetch_raw_cases_futures.extend(
                executor.submit(self._get_raw_cases_for_api_group, group)
                for group in all_api_groups
            )

        try:
            for task in concurrent.futures.as_completed(
                fetch_raw_cases_futures,
                timeout=self._timeouts["fetch_raw_cases"],
            ):
                raw_cases_for_group = task.result()
                fetched_cases.extend(raw_cases_for_group)
        except concurrent.futures.TimeoutError:
            # This happens, but it is not an error as such. We also want to continue
            # execution with the cases we _did_ manage to resolve.
            logger.warning("Timed out fetching raw cases for group", exc_info=True)
        except BaseException:
            logger.exception("Unhandled error fetching raw cases")

        # Resolve cases
        # Submit all futures and track which futures belong to which case
        all_futures: list[concurrent.futures.Future[None]] = []
        case_futures: dict[ZaakWithApiGroup, list[concurrent.futures.Future[None]]] = (
            defaultdict(list)
        )

        resolver_functions = [
            self._resolve_resultaat_and_resultaat_type,
            self._resolve_status_and_status_type,
            self._resolve_zaak_type,
        ]

        with parallel(max_workers=self._max_workers) as executor:
            for case_with_group in fetched_cases:
                # We have three independent resolver functions we want to resolve
                # concurrently. Only if all three tasks complete do we want to
                # add the case to the final list of resolved cases. Therefore, we keep
                # track of the futures on a per-case basis to be able to verify all
                # futures completed once the timeout has elapsed.
                for func in resolver_functions:
                    future = executor.submit(func, case_with_group)
                    all_futures.append(future)
                    case_futures[case_with_group].append(future)

        # Wait for futures to complete or timeout
        try:
            concurrent.futures.wait(
                all_futures,
                timeout=self._timeouts["resolve_cases"],
            )
        except concurrent.futures.TimeoutError:
            # This happens, but it is not an error as such. We also want to
            # continue execution with the cases we _did_ manage to resolve.
            logger.warning("Timed out resolving cases", exc_info=True)
        except BaseException:
            logger.exception("Unhandled error during zaak resolution")

        # Now check which cases had all 3 futures complete successfully. If we did not
        # manage to complete the resolutions for zaak, status and resultaat type, we
        # exclude the case from the final list.
        resolved_cases: list[ZaakWithApiGroup] = []
        for zaak, futures in case_futures.items():
            # Check if all 3 futures completed without exceptions...
            if not all(f.done() and not f.exception() for f in futures):
                logger.warning(
                    "Culling zaak %s because not all resolutions completed successfully",
                    zaak.identification,
                )
                # ... unable to fully resolve, leave it out of the list
                continue

            zaak_with_resolved_zgw_refs = self._replace_catalogus_api_with_model_refs(
                zaak
            )

            if is_zaak_visible(zaak_with_resolved_zgw_refs.zaak):
                resolved_cases.append(zaak_with_resolved_zgw_refs)
            else:
                logger.debug(
                    "Culling zaak %s because it is invisible",
                    zaak_with_resolved_zgw_refs.identification,
                )

        # Filter and sort cases
        resolved_cases.sort(key=lambda case: case.zaak.startdatum, reverse=True)
        resolved_cases.sort(key=lambda c: all_api_groups.index(c.api_group))
        return resolved_cases

    def _replace_catalogus_api_with_model_refs(
        self,
        zaak_with_api_group: ZaakWithApiGroup,
    ) -> ZaakWithApiGroup:
        try:
            zaaktype_config = ZaakTypeConfig.objects.filter_case_type(
                zaak_with_api_group.zaak.zaaktype
            ).get()

            logger.debug(
                "Resolved zaaktype URL to config",
                zaaktype_url=zaak_with_api_group.zaak.zaaktype.url,
                zaaktype_config=zaaktype_config,
            )
            zaak_with_api_group.zaak.zaaktype_config = zaaktype_config

            if zaaktype_config and zaak_with_api_group.zaak.status:
                statustype_config = ZaakTypeStatusTypeConfig.objects.get(
                    zaaktype_config=zaaktype_config,
                    statustype_url=zaak_with_api_group.zaak.status.statustype.url,
                )
                zaak_with_api_group.zaak.statustype_config = statustype_config
        except ZaakTypeConfig.DoesNotExist:
            logger.warning(
                "No matching ZaakTypeConfig for type",
                zaaktype_url=zaak_with_api_group.zaak.zaaktype.url,
            )
        except ZaakTypeStatusTypeConfig.DoesNotExist:
            logger.warning(
                "No matching ZaakTypeStatusTypeConfig_config for statustype_url",
                statustype_url=zaak_with_api_group.zaak.status.statustype.url,
                exc_info=True,
            )

        return zaak_with_api_group

    def _resolve_zaak_type(
        self,
        zaak_with_group: ZaakWithApiGroup,
    ) -> None:
        """
        Resolve `case.zaaktype` (`str`) to a `ZaakType(ZGWModel)` object

        Note: the result of `fetch_single_case_type` is cached, hence a request
            is only made for new case type urls
        """
        client = CaseListService._catalogi_client_factory(zaak_with_group.api_group)
        if not isinstance(zaak_with_group.zaak.zaaktype, str):
            logger.debug(
                "Case %s already has a resolved zaaktype",
                zaak_with_group.zaak.identificatie,
            )
            return

        case_type = client.fetch_single_case_type(zaak_with_group.zaak.zaaktype)
        if not case_type:
            raise ResolveCaseException(
                f"Unable to resolve zaaktype for url: {zaak_with_group.zaak.zaaktype}"
            )

        with self._zaak_update_lock:
            zaak_with_group.zaak.zaaktype = case_type

    def _resolve_status_and_status_type(
        self,
        zaak_with_group: ZaakWithApiGroup,
    ) -> None:
        zaken_client = CaseListService._zaken_client_factory(zaak_with_group.api_group)
        catalogi_client = CaseListService._catalogi_client_factory(
            zaak_with_group.api_group
        )

        if not isinstance(zaak_with_group.zaak.status, str):
            raise ResolveCaseException(
                f"`case.status` for case {zaak_with_group.zaak.identificatie} "
                f"is not a str but {type(zaak_with_group.zaak.status)}"
            )

        status = zaken_client.fetch_single_status(zaak_with_group.zaak.status)
        if not status:
            raise ResolveCaseException(
                f"Unable to resolve status {zaak_with_group.zaak.status} "
                f"for case {zaak_with_group.zaak.identificatie}"
            )

        status_type = catalogi_client.fetch_single_status_type(status.statustype)
        if not status_type:
            raise ResolveCaseException(
                f"Unable to resolve status_type {status.statustype} "
                f"for case {zaak_with_group.zaak.identificatie}"
            )

        with self._zaak_update_lock:
            zaak_with_group.zaak.status = status
            zaak_with_group.zaak.status.statustype = status_type

    def _resolve_resultaat_and_resultaat_type(
        self,
        zaak_with_group: ZaakWithApiGroup,
    ) -> None:
        # Note this is not a failure: the zaak has no resultaat, nothing to do.
        if zaak_with_group.zaak.resultaat is None:
            return

        zaken_client = CaseListService._zaken_client_factory(zaak_with_group.api_group)
        catalogi_client = CaseListService._catalogi_client_factory(
            zaak_with_group.api_group
        )

        if not isinstance(zaak_with_group.zaak.resultaat, str):
            raise ResolveCaseException(
                f"`case.resultaat` for case {zaak_with_group.zaak.identificatie} "
                f"is not a str but {type(zaak_with_group.zaak.resultaat)}"
            )

        resultaat = zaken_client.fetch_single_result(zaak_with_group.zaak.resultaat)
        if not resultaat:
            raise ResolveCaseException(
                f"Unable to fetch resultaat for {zaak_with_group.zaak}"
            )

        resultaattype = catalogi_client.fetch_single_resultaat_type(
            resultaat.resultaattype
        )
        if not resultaattype:
            raise ResolveCaseException(
                f"Unable to resolve resultaattype for {resultaat.resultaattype}"
            )

        with self._zaak_update_lock:
            zaak_with_group.zaak.resultaat = resultaat
            zaak_with_group.zaak.resultaat.resultaattype = resultaattype
