import concurrent.futures
import enum
import threading
from collections import Counter, defaultdict
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


class SkipReason(enum.Enum):
    """Reasons why a case was skipped/filtered out."""

    RESOLUTION_FAILED = "resolution_failed"
    NOT_VISIBLE = "not_visible"
    TIMEOUT = "timeout"


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


@dataclass
class SkippedZaak:
    """Information about a zaak that was skipped."""

    zaak: ZaakWithApiGroup
    reason: SkipReason
    details: str | None = None


@dataclass
class ZakenResult:
    """Result from fetching and processing zaken."""

    zaken: list[ZaakWithApiGroup]
    skipped: list[SkippedZaak]

    @property
    def total_fetched(self) -> int:
        """Total number of zaken fetched (visible + skipped)."""
        return len(self.zaken) + len(self.skipped)

    def get_skip_statistics(self) -> dict[SkipReason, int]:
        """Return statistics about why zaken were skipped."""
        stats = dict(Counter(skipped.reason for skipped in self.skipped))
        # Ensure all SkipReason values are present with 0 as default
        for reason in SkipReason:
            stats.setdefault(reason, 0)
        return stats


class Timeouts(TypedDict):
    fetch_raw_zaken: int | float
    resolve_zaken: int | float
    fetch_formulieren: int | float


class CaseListService:
    _max_workers: int
    _timeouts: Timeouts

    @classmethod
    def from_request(cls, request: HttpRequest) -> "CaseListService":
        """
        Factory method to create a CaseListService from a Django request.

        Raises:
            ValueError: If the user is not authenticated or has no identity fields.
        """
        user = request.user
        if not user.is_authenticated:
            raise ValueError("User must be authenticated to use CaseListService")

        # Get identity parameters from the request
        params = get_user_fetch_parameters(request, use_rsin=False)
        if not params:
            raise ValueError("User must have either BSN or KVK to use CaseListService")

        # For eHerkenning users, also get RSIN (which isn't in params by default)
        if "user_kvk" in params:
            params["user_rsin"] = getattr(user, "rsin", None)

        return cls(identity_params=params)

    def __init__(self, identity_params: dict[str, str]):
        """
        Initialize CaseListService with identity parameters.

        Args:
            identity_params: Dictionary with identity fields matching the format
                returned by get_user_fetch_parameters. Must contain either:
                - user_bsn: BSN for natural persons
                - user_kvk: KVK number for companies (optionally with user_rsin
                  and/or vestigingsnummer)

        Raises:
            ValueError: If params don't contain valid identity information.
        """
        # Validate that we have exactly one identity type
        has_bsn = "user_bsn" in identity_params
        has_kvk = "user_kvk" in identity_params

        if has_bsn and has_kvk:
            raise ValueError("Cannot have both user_bsn and user_kvk")

        if not has_bsn and not has_kvk:
            raise ValueError("Must have either user_bsn or user_kvk")

        # RSIN and vestiging are only valid with KVK
        if has_bsn and (
            "user_rsin" in identity_params or "vestigingsnummer" in identity_params
        ):
            raise ValueError(
                "user_rsin and vestigingsnummer are only valid with user_kvk"
            )

        # Store the base parameters
        self._identity_params = identity_params

        self._timeouts = {
            "fetch_raw_zaken": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.3,
            "resolve_zaken": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.5,
            "fetch_formulieren": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.2,
        }
        self._max_workers = settings.ZGW_CASE_LIST_NUM_WORKERS

        logger.debug(
            "Configured CaseListService",
            timeouts=self._timeouts,
            max_workers=self._max_workers,
            identity_params={k: bool(v) for k, v in identity_params.items()},
        )

        # Our resolver functions modify the case list in-place, the lock is used to
        # ensure there are no concurrent writes
        self._zaak_update_lock = threading.RLock()

    def _get_fetch_parameters(self, use_rsin: bool = True) -> dict:
        """
        Build fetch parameters dict for API calls.

        Args:
            use_rsin: If True and user_rsin is available, use it instead of user_kvk
                for eHerkenning users (some APIs require this).

        Returns:
            Dictionary with identity parameters suitable for passing to API clients.
        """
        if "user_bsn" in self._identity_params:
            return {"user_bsn": self._identity_params["user_bsn"]}

        # KVK case - potentially swap kvk for rsin
        params = dict(self._identity_params)

        if use_rsin and "user_rsin" in params:
            # Replace user_kvk with user_rsin
            params.pop("user_kvk", None)
        else:
            # Keep user_kvk, remove user_rsin
            params.pop("user_rsin", None)

        return params

    @staticmethod
    def _zaken_client_factory(group: ZGWApiGroupConfig):
        return cast(
            ZakenClient,
            build_zgw_client_from_service(
                group.zrc_service,
                use_openzaak_120_params=group.fetch_eherkenning_zaken_with_openzaak_120_params,
                fetch_rollen_with_betrokkene_type=group.fetch_rollen_with_betrokkene_type,
            ),
        )

    @staticmethod
    def _catalogi_client_factory(group: ZGWApiGroupConfig):
        return cast(CatalogiClient, build_zgw_client_from_service(group.ztc_service))

    def _get_formulieren_for_api_group(
        self, group: ZGWApiGroupConfig
    ) -> list[FormulierWithApiGroup]:
        if not group.forms_client:
            raise ValueError(f"{group} has no `forms_client`")

        # Note: fetch_formulieren doesn't support user_rsin, only user_bsn/user_kvk
        params = self._get_fetch_parameters(use_rsin=False)
        formulieren = group.forms_client.fetch_formulieren(**params)

        return [
            FormulierWithApiGroup(
                formulier=formulier,
                api_group=group,
                type_aanvraag=TypeAanvraag.FORMULIER,
            )
            for formulier in formulieren
        ]

    def get_formulieren(self) -> list[FormulierWithApiGroup]:
        all_api_groups = list(
            ZGWApiGroupConfig.objects.filter(form_service__isnull=False).select_related(
                "form_service",
            )
        )

        subs_with_api_group: list[FormulierWithApiGroup] = []
        with parallel(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(self._get_formulieren_for_api_group, group)
                for group in all_api_groups
            ]

            try:
                for task in concurrent.futures.as_completed(
                    futures,
                    timeout=self._timeouts["fetch_formulieren"],
                ):
                    try:
                        subs_with_api_group.extend(task.result())
                    except BaseException:
                        logger.exception("Error fetching and pre-processing zaken")
            except concurrent.futures.TimeoutError:
                logger.warning("Timeout while fetching formulieren")

        # Sort formulieren by date modified
        subs_with_api_group.sort(
            key=lambda sub: sub.formulier.datum_laatste_wijziging, reverse=True
        )

        return subs_with_api_group

    @staticmethod
    def get_zaak_filter_status(zaak: Zaak) -> CaseFilterFormOption:
        if zaak.einddatum:
            return CaseFilterFormOption.ZAAK_AFGEROND

        return CaseFilterFormOption.ZAAK_OPEN

    def get_zaak_status_frequencies(
        self,
        zaken: Iterable[ZaakWithApiGroup],
        formulieren: Iterable[FormulierWithApiGroup],
    ) -> dict[CaseFilterFormOption, int]:
        zaak_statuses = [self.get_zaak_filter_status(zaak.zaak) for zaak in zaken]

        # add static text for formulieren
        zaak_statuses += [CaseFilterFormOption.FORMULIER for _ in formulieren]

        return {
            status: zaak_statuses.count(status) for status in list(CaseFilterFormOption)
        }

    def _get_raw_zaken_for_api_group(
        self, group: ZGWApiGroupConfig
    ) -> list[ZaakWithApiGroup]:
        # Use user_rsin if the API group is configured to use it for eHerkenning
        use_rsin = group.fetch_eherkenning_zaken_with_rsin
        params = self._get_fetch_parameters(use_rsin=use_rsin)
        raw_zaken = group.zaken_client.fetch_zaken(**params)

        return [
            ZaakWithApiGroup(
                zaak=raw_zaak, api_group=group, type_aanvraag=TypeAanvraag.ZAAK
            )
            for raw_zaak in raw_zaken
        ]

    def get_zaken(self) -> ZakenResult:
        all_api_groups = list(
            ZGWApiGroupConfig.objects.select_related(
                "zrc_service",
                "ztc_service",
                "drc_service",
                "form_service",
            ).all()
        )

        # Get the raw zaken for all groups
        fetched_zaken: list[ZaakWithApiGroup] = []
        fetch_raw_zaken_futures: list[
            concurrent.futures.Future[list[ZaakWithApiGroup]]
        ] = []
        with parallel(max_workers=self._max_workers) as executor:
            fetch_raw_zaken_futures.extend(
                executor.submit(self._get_raw_zaken_for_api_group, group)
                for group in all_api_groups
            )

            try:
                for task in concurrent.futures.as_completed(
                    fetch_raw_zaken_futures,
                    timeout=self._timeouts["fetch_raw_zaken"],
                ):
                    raw_zaken_for_group = task.result()
                    fetched_zaken.extend(raw_zaken_for_group)
            except concurrent.futures.TimeoutError:
                # This happens, but it is not an error as such. We also want to continue
                # execution with the zaken we _did_ manage to resolve.
                logger.warning("Timed out fetching raw zaken for group", exc_info=True)
            except BaseException:
                logger.exception("Unhandled error fetching raw zaken")

        # Resolve zaken
        # Submit all futures and track which futures belong to which case
        all_futures: list[concurrent.futures.Future[None]] = []
        zaak_futures: dict[ZaakWithApiGroup, list[concurrent.futures.Future[None]]] = (
            defaultdict(list)
        )

        resolver_functions = [
            self._resolve_resultaat_and_resultaat_type,
            self._resolve_status_and_status_type,
            self._resolve_zaak_type,
        ]

        with parallel(max_workers=self._max_workers) as executor:
            for zaak_with_group in fetched_zaken:
                # We have three independent resolver functions we want to resolve
                # concurrently. Only if all three tasks complete do we want to
                # add the zaak to the final list of resolved zaken. Therefore, we keep
                # track of the futures on a per-zaak basis to be able to verify all
                # futures completed once the timeout has elapsed.
                for func in resolver_functions:
                    future = executor.submit(func, zaak_with_group)
                    all_futures.append(future)
                    zaak_futures[zaak_with_group].append(future)

            # Wait for futures to complete or timeout
            try:
                concurrent.futures.wait(
                    all_futures,
                    timeout=self._timeouts["resolve_zaken"],
                )
            except concurrent.futures.TimeoutError:
                # This happens, but it is not an error as such. We also want to
                # continue execution with the zaken we _did_ manage to resolve.
                logger.warning("Timed out resolving zaken", exc_info=True)
            except BaseException:
                logger.exception("Unhandled error during zaak resolution")

        # Now check which zaken had all 3 futures complete successfully. If we did not
        # manage to complete the resolutions for zaak, status and resultaat type, we
        # exclude the case from the final list.
        resolved_zaken: list[ZaakWithApiGroup] = []
        skipped_zaken: list[SkippedZaak] = []

        for zaak, futures in zaak_futures.items():
            # Check if all 3 futures completed without exceptions...
            if not all(f.done() and not f.exception() for f in futures):
                # Collect exception details
                exceptions = [f.exception() for f in futures if f.exception()]
                details = (
                    "; ".join(str(e) for e in exceptions)
                    if exceptions
                    else "incomplete"
                )

                logger.warning(
                    "Culling zaak %s because not all resolutions completed successfully",
                    zaak.identification,
                    details=details,
                )

                # Track this as a skipped zaak
                skipped_zaken.append(
                    SkippedZaak(
                        zaak=zaak,
                        reason=SkipReason.RESOLUTION_FAILED,
                        details=details,
                    )
                )
                # ... unable to fully resolve, leave it out of the list
                continue

            zaak_with_resolved_zgw_refs = self._replace_catalogus_api_with_model_refs(
                zaak
            )

            if is_zaak_visible(zaak_with_resolved_zgw_refs.zaak):
                resolved_zaken.append(zaak_with_resolved_zgw_refs)
            else:
                logger.debug(
                    "Culling zaak %s because it is invisible",
                    zaak_with_resolved_zgw_refs.identification,
                )

                # Track this as a skipped zaak
                skipped_zaken.append(
                    SkippedZaak(
                        zaak=zaak_with_resolved_zgw_refs,
                        reason=SkipReason.NOT_VISIBLE,
                        details=f"Confidentiality: {zaak_with_resolved_zgw_refs.zaak.vertrouwelijkheidaanduiding}",
                    )
                )

        # Sort by startdatum (newest first), using api_group index as tiebreaker
        resolved_zaken.sort(
            key=lambda c: (
                -c.zaak.startdatum.toordinal(),
                all_api_groups.index(c.api_group),
            )
        )

        return ZakenResult(zaken=resolved_zaken, skipped=skipped_zaken)

    def _replace_catalogus_api_with_model_refs(
        self,
        zaak_with_api_group: ZaakWithApiGroup,
    ) -> ZaakWithApiGroup:
        try:
            zaaktype_config = ZaakTypeConfig.objects.filter_zaak_type(
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

        Note: the result of `fetch_single_zaaktype` is cached, hence a request
            is only made for new case type urls
        """
        client = CaseListService._catalogi_client_factory(zaak_with_group.api_group)
        if not isinstance(zaak_with_group.zaak.zaaktype, str):
            logger.debug(
                "Case %s already has a resolved zaaktype",
                zaak_with_group.zaak.identificatie,
            )
            return

        zaaktype = client.fetch_single_zaaktype(zaak_with_group.zaak.zaaktype)
        if not zaaktype:
            raise ResolveCaseException(
                f"Unable to resolve zaaktype for url: {zaak_with_group.zaak.zaaktype}"
            )

        with self._zaak_update_lock:
            zaak_with_group.zaak.zaaktype = zaaktype

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
