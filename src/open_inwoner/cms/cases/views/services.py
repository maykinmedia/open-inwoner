import concurrent.futures
import enum
import logging
import threading
from dataclasses import dataclass
from typing import TypedDict, cast

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from zgw_consumers.concurrent import parallel

from open_inwoner.openzaak.api_models import OpenSubmission, Zaak
from open_inwoner.openzaak.clients import (
    CatalogiClient,
    ZakenClient,
    build_zgw_client_from_service,
)
from open_inwoner.openzaak.models import (
    ZaakTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
)
from open_inwoner.openzaak.utils import get_user_fetch_parameters, is_zaak_visible

logger = logging.getLogger(__name__)


class CaseFilterFormOption(enum.Enum):
    OPEN_SUBMISSION = _("Openstaande formulieren")
    OPEN_CASE = _("Lopende aanvragen")
    CLOSED_CASE = _("Afgeronde aanvragen")


@dataclass(frozen=True)
class ZaakWithApiGroup:
    zaak: Zaak
    api_group: ZGWApiGroupConfig

    @property
    def identification(self) -> str:
        return self.zaak.url

    def process_data(self) -> dict:
        return {**self.zaak.process_data(), "api_group": self.api_group}

    def __hash__(self):
        return hash((self.identification, self.api_group.pk))


@dataclass(frozen=True)
class SubmissionWithApiGroup:
    submission: OpenSubmission
    api_group: ZGWApiGroupConfig

    @property
    def identification(self) -> str:
        return self.submission.url

    def process_data(self) -> dict:
        return {**self.submission.process_data(), "api_group": self.api_group}

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
            "Configured CaseListService with timeouts=%s and worker limit=%s",
            repr(self._timeouts),
            self._max_workers,
        )

        # Our resolver functions modify the case list in-place, the lock is used to
        # ensure there are no concurrent writes
        self._zaak_update_lock = threading.RLock()

    @staticmethod
    def _zaken_client_factory(group: ZGWApiGroupConfig):
        return cast(ZakenClient, build_zgw_client_from_service(group.zrc_service))

    @staticmethod
    def _catalogi_client_factory(group: ZGWApiGroupConfig):
        return cast(CatalogiClient, build_zgw_client_from_service(group.ztc_service))

    def _get_submissions_for_api_group(
        self, group: ZGWApiGroupConfig
    ) -> list[SubmissionWithApiGroup]:
        if not group.forms_client:
            raise ValueError(f"{group} has no `forms_client`")

        return [
            SubmissionWithApiGroup(submission=sub, api_group=group)
            for sub in group.forms_client.fetch_open_submissions(
                **get_user_fetch_parameters(
                    self.request, use_rsin=group.fetch_eherkenning_zaken_with_rsin
                )
            )
        ]

    def get_submissions(self) -> list[SubmissionWithApiGroup]:
        all_api_groups = list(
            ZGWApiGroupConfig.objects.filter(form_service__isnull=False).select_related(
                "form_service",
            )
        )

        subs_with_api_group: list[SubmissionWithApiGroup] = []
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
            key=lambda sub: sub.submission.datum_laatste_wijziging, reverse=True
        )

        return subs_with_api_group

    @staticmethod
    def get_case_filter_status(zaak: Zaak) -> CaseFilterFormOption:
        if zaak.einddatum:
            return CaseFilterFormOption.CLOSED_CASE

        return CaseFilterFormOption.OPEN_CASE

    def get_case_status_frequencies(self) -> dict[CaseFilterFormOption, int]:
        cases = self.get_cases()
        submissions = self.get_submissions()

        case_statuses = [self.get_case_filter_status(case.zaak) for case in cases]

        # add static text for open submissions
        case_statuses += [CaseFilterFormOption.OPEN_SUBMISSION for _ in submissions]

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
            ZaakWithApiGroup(zaak=raw_cases, api_group=group) for raw_cases in raw_cases
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
        resolve_cases_futures: dict[
            ZaakWithApiGroup, list[concurrent.futures.Future[ZaakWithApiGroup]]
        ] = {}
        with parallel(max_workers=self._max_workers) as executor:
            for case_with_group in fetched_cases:
                # We have three independent resolvers functions we want to resolve
                # concurrently. Only if all three tasks complete do we want to
                # add the case to the final list of resolved cases. Therefore, we keep
                # track of the futures on a per-case basis to be able to verify all
                # futures completed once the wait call has elapsed.
                resolve_cases_futures.update(
                    {
                        case_with_group: [
                            executor.submit(func, case_with_group)
                            for func in (
                                self._resolve_resultaat_and_resultaat_type,
                                self._resolve_status_and_status_type,
                                self._resolve_zaak_type,
                            )
                        ]
                    }
                )

        try:
            concurrent.futures.wait(
                (f for future in resolve_cases_futures.values() for f in future),
                timeout=self._timeouts["resolve_cases"],
            )
        except concurrent.futures.TimeoutError:
            # This happens, but it is not an error as such. We also want to
            # continue execution with the cases we _did_ manage to resolve.
            logger.warning("Timed out resolving cases", exc_info=True)
        except BaseException:
            logger.exception("Unhandled error resolving zaak")

        resolved_cases: list[ZaakWithApiGroup] = []
        for zaak, futures in resolve_cases_futures.items():
            # Did all resolutions complete for this case? Note that we care about
            # success specifically: cancellation or exceptions mean we discard the case
            # from the final list.
            for f in futures:
                try:
                    f.result()
                except BaseException:
                    logger.debug(
                        "Culling zaak %s because it lacks a result",
                        zaak.identification,
                    )
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
                "Resolved %s to %s",
                zaak_with_api_group.zaak.zaaktype.url,
                zaaktype_config,
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
                "No matching ZaakTypeConfig for type=%s",
                zaak_with_api_group.zaak.zaaktype.url,
            )
        except ZaakTypeStatusTypeConfig.DoesNotExist:
            logger.warning(
                "No matching ZaakTypeStatusTypeConfig_config for statustype_url=%s",
                zaak_with_api_group.zaak.status.statustype.url,
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
            logger.error(
                "Unable to resolve zaaktype for url: %s", zaak_with_group.zaak.zaaktype
            )
            return

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
            logger.error(
                "`case.status` for case %s is not a str but %s",
                zaak_with_group.zaak.identificatie,
                type(zaak_with_group.zaak.status),
            )
            return

        status = zaken_client.fetch_single_status(zaak_with_group.zaak.status)
        if not status:
            logger.error(
                "Unable to resolve status %s for case %s",
                zaak_with_group.zaak.status,
                zaak_with_group.zaak.identificatie,
            )
            return

        status_type = catalogi_client.fetch_single_status_type(status.statustype)
        if not status_type:
            logger.error(
                "Unable to resolve status_type %s for case %s",
                status.statustype,
                zaak_with_group.zaak.identificatie,
            )
            return

        with self._zaak_update_lock:
            zaak_with_group.zaak.status = status
            zaak_with_group.zaak.status.statustype = status_type

    def _resolve_resultaat_and_resultaat_type(
        self,
        zaak_with_group: ZaakWithApiGroup,
    ) -> None:
        zaken_client = CaseListService._zaken_client_factory(zaak_with_group.api_group)
        catalogi_client = CaseListService._catalogi_client_factory(
            zaak_with_group.api_group
        )

        if zaak_with_group.zaak.resultaat is None:
            return

        if not isinstance(zaak_with_group.zaak.resultaat, str):
            logger.error(
                "`case.resultaat` for case %s is not a str but %s",
                zaak_with_group.zaak.identificatie,
                type(zaak_with_group.zaak.resultaat),
            )
            return

        resultaat = zaken_client.fetch_single_result(zaak_with_group.zaak.resultaat)
        if not resultaat:
            logger.error("Unable to fetch resultaat for %s", zaak_with_group.zaak)
            return

        resultaattype = catalogi_client.fetch_single_resultaat_type(
            resultaat.resultaattype
        )
        if not resultaattype:
            logger.error(
                "Unable to resolve resultaattype for %s", resultaat.resultaattype
            )
            return

        with self._zaak_update_lock:
            zaak_with_group.zaak.resultaat = resultaat
            zaak_with_group.zaak.resultaat.resultaattype = resultaattype

        return
