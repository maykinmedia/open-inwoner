from __future__ import annotations

import concurrent.futures
import contextlib
import enum
import threading
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from typing import Generic, NoReturn, Self, TypedDict, TypeVar, cast

from django.utils.functional import cached_property

import structlog
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.user_identification import (
    BSNIdentification,
    KVKIdentification,
    UserIdentification,
)
from open_inwoner.openzaak.api_models import (
    Formulier,
    InformatieObject,
    OpenstaandeTaak,
    ResultaatType,
    Rol,
    Status,
    StatusType,
    Zaak,
    ZaakInformatieObject,
    ZaakType,
)
from open_inwoner.openzaak.clients import (
    CatalogiClient,
    DocumentenClient,
    FormulierenClient,
    ZakenClient,
    build_zgw_client_from_service,
)
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.exceptions import ZgwAPIError
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
)
from open_inwoner.openzaak.utils import (
    get_role_name_display,
    is_object_visible,
)
from open_inwoner.utils.concurrency import TimedParallel

logger = structlog.stdlib.get_logger(__name__)


class ResolveCaseException(Exception):
    pass


@dataclass
class ZaakDocumentData:
    """Raw document data; view builds FileItem with URL."""

    case_info_obj: ZaakInformatieObject
    info_obj: InformatieObject


@dataclass
class ZaakDetailData:
    """All ZGW API data fetched for the zaak detail page."""

    statuses: list[Status]
    statustypen: list[StatusType]
    status_types_mapping: dict[str, StatusType]
    documents: list[ZaakDocumentData]
    result: dict
    initiator: str


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


class ZaakWithApiGroupZaakTypeResolved(ZaakWithApiGroup):
    """ZaakWithApiGroup whose zaaktype has been resolved from URL to ZaakType."""


class ZaakWithApiGroupFullyResolved(ZaakWithApiGroupZaakTypeResolved):
    """ZaakWithApiGroup with zaaktype, status, and resultaat all resolved."""


class SkipReason(enum.Enum):
    NO_STATUS = "no_status"
    NO_ZAAKTYPE = "no_zaaktype"
    INTERNAL_ZAAKTYPE = "internal_zaaktype"
    CONFIDENTIALITY_TOO_HIGH = "confidentiality_too_high"
    BEFORE_VISIBLE_FROM_DATE = "before_visible_from_date"
    ROL_RESOLUTION_FAILED = "rol_resolution_failed"
    ZAAKTYPE_RESOLUTION_FAILED = "zaaktype_resolution_failed"
    STATUS_RESOLUTION_FAILED = "status_resolution_failed"
    STATUSTYPE_RESOLUTION_FAILED = "statustype_resolution_failed"
    RESULTAAT_RESOLUTION_FAILED = "resultaat_resolution_failed"
    RESULTAATTYPE_RESOLUTION_FAILED = "resultaattype_resolution_failed"
    RESOLUTION_FAILED = "resolution_failed"
    TIMEOUT = "timeout"

    @classmethod
    def resolution_failures(cls) -> frozenset[Self]:
        """Reasons for a ZGW entity of the zaak failing to resolve.

        Each entity fetched while building the case list gets its own reason;
        `RESOLUTION_FAILED` is the fallback for a failure that could not be
        attributed to a specific entity.
        """
        return frozenset(
            {
                cls.ROL_RESOLUTION_FAILED,
                cls.ZAAKTYPE_RESOLUTION_FAILED,
                cls.STATUS_RESOLUTION_FAILED,
                cls.STATUSTYPE_RESOLUTION_FAILED,
                cls.RESULTAAT_RESOLUTION_FAILED,
                cls.RESULTAATTYPE_RESOLUTION_FAILED,
                cls.RESOLUTION_FAILED,
            }
        )

    @classmethod
    def transient_reasons(cls) -> frozenset[Self]:
        """Zaken skipped for these reasons may show up on retry"""
        return cls.resolution_failures() | {cls.TIMEOUT}


class ZaakResolutionError(ResolveCaseException):
    """A ZGW entity associated with a zaak could not be resolved.

    Carries the `SkipReason` naming that entity, so callers can report which part
    of the zaak failed instead of a blanket resolution failure.
    """

    def __init__(self, reason: SkipReason, message: str = ""):
        super().__init__(message or reason.value)
        self.reason = reason


@dataclass
class SkippedZaak:
    zaak_url: str
    # A zaak has several resolution steps, each of which can fail on its own, so a
    # single zaak can be skipped for more than one reason
    reasons: frozenset[SkipReason]
    api_group: ZGWApiGroupConfig


_ZaakT = TypeVar("_ZaakT", bound=ZaakWithApiGroup)


@dataclass
class ZakenResult(Generic[_ZaakT]):
    zaken: list[_ZaakT]
    skipped: list[SkippedZaak]
    # Set when a whole-stage timeout or fetch error dropped zaken whose URLs are
    # unknown (the raw fetch stage), so `skipped` cannot enumerate them.
    raw_fetch_incomplete: bool = False

    @property
    def is_incomplete(self) -> bool:
        """Whether results are incomplete because of a timeout or fetch/resolve error.

        Zaken excluded for confidentiality, an internal zaaktype or a
        before-visible-from date are legitimately absent and retrying will not
        bring them back.
        """
        return self.raw_fetch_incomplete or any(
            not skipped.reasons.isdisjoint(SkipReason.transient_reasons())
            for skipped in self.skipped
        )


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
class FormulierenResult:
    formulieren: list[FormulierWithApiGroup]
    # Set when the fetch stage timed out, so the list may be incomplete.
    timed_out: bool = False


class Timeouts(TypedDict):
    get_raw_zaken: int | float
    get_visible_zaken: int | float
    fully_resolve_zaken: int | float
    get_formulieren: int | float


class ZGWService:
    _max_workers: int | None

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    def __init__(self, use_cache: bool = True):
        self._use_cache = use_cache
        self._max_workers = OpenZaakConfig.get_solo().case_list_num_workers
        # Resolvers mutate Zaak fields in parallel futures; the lock prevents concurrent writes.
        self._zaak_update_lock = threading.RLock()

        logger.debug("Configured ZGWService", max_workers=self._max_workers)

    @staticmethod
    def _case_list_stage_timeouts(config: OpenZaakConfig | None = None) -> Timeouts:
        """Split the case-list time budget across pipeline stages.

        The total budget is a global setting because all groups participate in every
        stage under a single concurrent timeout. The fractions must sum to 1.

        These are independent per-stage ceilings, not fractions of one
        continuously ticking deadline shared across the whole request: each
        stage builds its own `TimedParallel` with its own clock (see that
        class's docstring for exactly when it starts), and the stages run
        sequentially. A stage that finishes well under its share does not
        donate the leftover time to the next one - so `case_list_fetch_timeout`
        is a soft target for the sum of the stages, not a hard cap actually
        enforced on the request as a whole; worst case, the call can approach
        the sum of all four budgets.
        """
        config = config or OpenZaakConfig.get_solo()

        t = config.case_list_fetch_timeout
        return {
            "get_raw_zaken": t * 0.3,
            "get_visible_zaken": t * 0.2,
            "fully_resolve_zaken": t * 0.3,
            "get_formulieren": t * 0.2,
        }

    @staticmethod
    def _zaken_client_factory(
        group: ZGWApiGroupConfig, config: OpenZaakConfig | None = None
    ) -> ZakenClient:
        if config is None:
            config = OpenZaakConfig.get_solo()
        return cast(
            ZakenClient,
            build_zgw_client_from_service(
                group.zrc_service,
                use_openzaak_120_params=group.fetch_eherkenning_zaken_with_openzaak_120_params,
                fetch_rollen_with_betrokkene_type=group.fetch_rollen_with_betrokkene_type,
                zaak_max_confidentiality=config.zaak_max_confidentiality,
                limit_user_visible_cases_to_role=config.limit_user_visible_cases_to_role,
                cache_zaken_timeout=group.cache_zaken_timeout,
            ),
        )

    @staticmethod
    def _catalogi_client_factory(group: ZGWApiGroupConfig) -> CatalogiClient:
        return cast(
            CatalogiClient,
            build_zgw_client_from_service(
                group.ztc_service,
                cache_catalogi_timeout=group.cache_catalogi_timeout,
            ),
        )

    @staticmethod
    def _documenten_client_factory(group: ZGWApiGroupConfig) -> DocumentenClient:
        return cast(
            DocumentenClient,
            build_zgw_client_from_service(
                group.drc_service,
                cache_zaken_timeout=group.cache_zaken_timeout,
            ),
        )

    @staticmethod
    def _formulieren_client_factory(group: ZGWApiGroupConfig) -> FormulierenClient:
        """Caller must guarantee `group.form_service` is set (it is nullable).

        Select groups with `ZGWApiGroupConfigQuerySet.with_forms_service()`.
        Checking here anyway names the group that is misconfigured, instead of
        failing with an `AttributeError` on `None` from inside `build_client`.
        """
        if group.form_service is None:
            raise ValueError(f"{group} has no `form_service`")

        return cast(
            FormulierenClient, build_zgw_client_from_service(group.form_service)
        )

    @cached_property
    def _zaaktype_visible_from_dates(self) -> dict[tuple[str, str], date]:
        """
        Map (catalogus url, zaaktype identificatie) to the earliest startdatum a zaak
        of that zaaktype may have to still be visible. Only zaaktypes with a configured
        date appear in the map.

        Cached per service instance, which is constructed per request, so changes made
        by an admin take effect on the next request.
        """
        return {
            (catalogus_url, identificatie): visible_from
            for catalogus_url, identificatie, visible_from in ZaakTypeConfig.objects.filter(
                zaken_visible_from__isnull=False
            ).values_list("catalogus__url", "identificatie", "zaken_visible_from")
        }

    def _is_zaak_visible(self, zaak: Zaak) -> tuple[bool, SkipReason | None]:
        """Return (True, None) if the zaak should be shown, or (False, reason) if hidden."""
        config = OpenZaakConfig.get_solo()

        if isinstance(zaak.zaaktype, str):
            raise ValueError("expected zaak.zaaktype to be resolved from url to model")

        if not zaak.status and not config.show_cases_without_status:
            logger.info(
                "Ignoring zaak as not visible for users: zaak has no status and "
                "show_cases_without_status is disabled",
                zaak_url=zaak.url,
            )
            return False, SkipReason.NO_STATUS

        if not zaak.zaaktype:
            logger.info(
                "Ignoring zaak as not visible for users: zaak has no zaaktype",
                zaak_url=zaak.url,
            )
            return False, SkipReason.NO_ZAAKTYPE

        if zaak.zaaktype.indicatie_intern_of_extern != "extern":
            logger.info(
                "Ignoring zaak as not visible for users: zaaktype is intern",
                zaak_url=zaak.url,
            )
            return False, SkipReason.INTERNAL_ZAAKTYPE

        if not is_object_visible(zaak, config.zaak_max_confidentiality):
            return False, SkipReason.CONFIDENTIALITY_TOO_HIGH

        # support both url and resolved dataclass, as in
        # `ZaakTypeConfigQueryset.filter_catalogus`
        catalogus = zaak.zaaktype.catalogus
        catalogus_url = catalogus if isinstance(catalogus, str) else catalogus.url

        visible_from = self._zaaktype_visible_from_dates.get(
            (catalogus_url, zaak.zaaktype.identificatie)
        )
        if visible_from and zaak.startdatum < visible_from:
            logger.info(
                "Ignoring zaak as not visible for users: startdatum precedes the "
                "date configured for its zaaktype",
                zaak_url=zaak.url,
                visible_from=visible_from,
            )
            return False, SkipReason.BEFORE_VISIBLE_FROM_DATE

        return True, None

    @staticmethod
    def _user_has_required_rol(
        zaak_url: str,
        user_identification: UserIdentification,
        zaken_client: ZakenClient,
        use_rsin: bool,
        limit_access_to_role: str,
    ) -> bool:
        """
        Return True if the user may access this zaak based on their rollen.

        The user must hold at least one rol on the zaak, and when
        `OpenZaakConfig.limit_user_visible_cases_to_role` is configured, at least one
        of those rollen must match it.

        Note we deliberately do not log `user_identification`, which holds a BSN or KVK
        number.
        """
        rollen = zaken_client.fetch_rollen_for_user(
            zaak_url, user_identification, use_rsin=use_rsin
        )

        if not rollen:
            logger.info("zaak access denied: no rol for zaak", zaak_url=zaak_url)
            return False

        if limit_access_to_role and not any(
            rol.omschrijving_generiek == limit_access_to_role for rol in rollen
        ):
            logger.info(
                "zaak access denied: incorrect rol for zaak",
                zaak_url=zaak_url,
                required_role=limit_access_to_role,
            )
            return False

        return True

    @staticmethod
    def _is_info_object_visible(
        info_object: InformatieObject,
        max_confidentiality_level: str,
        document_visible_statuses: list[str],
    ) -> bool:
        """Return True if the informatieobject should be shown to the user."""
        if (
            document_visible_statuses
            and info_object.status not in document_visible_statuses
        ):
            logger.debug(
                "Ignoring informatieobject as not visible for user",
                info_object_url=info_object.url,
                info_object_status=info_object.status,
                document_visible_statuses=document_visible_statuses,
                status_filtering_active=True,
                status_visible=False,
            )
            return False

        return is_object_visible(info_object, max_confidentiality_level)

    # -------------------------------------------------------------------------
    # Zaak list
    # -------------------------------------------------------------------------

    def _get_raw_zaken_for_api_group(
        self,
        group: ZGWApiGroupConfig,
        user_identification: UserIdentification,
        zaken_client: ZakenClient,
        use_rsin: bool,
        zaak_identificatie: str | None = None,
    ) -> list[ZaakWithApiGroup]:
        raw_zaken = zaken_client.fetch_zaken(
            user_identification,
            use_rsin=use_rsin,
            identificatie=zaak_identificatie,
        )
        return [
            ZaakWithApiGroup(
                zaak=raw_zaak, api_group=group, type_aanvraag=TypeAanvraag.ZAAK
            )
            for raw_zaak in raw_zaken
        ]

    def get_raw_zaken(
        self,
        user_identification: UserIdentification,
        zaak_identificatie: str | None = None,
    ) -> ZakenResult[ZaakWithApiGroup]:
        """Fetch zaken without resolution. For PDC and cache seeding."""

        # Each thread gets its own zaken client because requests.Session is not
        # thread-safe. Pre-fetch OpenZaakConfig to avoid additional DB calls.
        config = OpenZaakConfig.get_solo()
        timeouts = self._case_list_stage_timeouts(config)

        all_api_groups = list(
            ZGWApiGroupConfig.objects.select_related("zrc_service").all()
        )

        fetched_zaken: list[ZaakWithApiGroup] = []
        raw_fetch_incomplete = False
        with TimedParallel(
            max_workers=self._max_workers, name="get_raw_zaken"
        ) as executor:
            futures = [
                executor.submit(
                    self._get_raw_zaken_for_api_group,
                    group,
                    user_identification,
                    self._zaken_client_factory(group, config),
                    group.fetch_eherkenning_zaken_with_rsin,
                    zaak_identificatie,
                )
                for group in all_api_groups
            ]
            result = executor.as_completed(
                futures, cancel_after=timeouts["get_raw_zaken"]
            )
            for task in result:
                try:
                    fetched_zaken.extend(task.result())
                except BaseException:
                    logger.exception("Error fetching raw zaken for group")
                    raw_fetch_incomplete = True

        if result.timed_out:
            logger.warning("Timed out fetching raw zaken")
            raw_fetch_incomplete = True

        return ZakenResult(
            zaken=fetched_zaken,
            skipped=[],
            raw_fetch_incomplete=raw_fetch_incomplete,
        )

    def search_zaken(
        self, user_identification: UserIdentification, zaak_identificatie: str
    ) -> ZakenResult[ZaakWithApiGroupZaakTypeResolved]:
        """
        Search for a zaak by zaak_identificatie across all API groups.

        Returns matches that are visible and for which the user holds a (sufficiently
        privileged) rol.
        """
        config = OpenZaakConfig.get_solo()
        limit_access_to_role = config.limit_user_visible_cases_to_role

        raw_result = self.get_raw_zaken(user_identification, zaak_identificatie)

        visible_zaken: list[ZaakWithApiGroupZaakTypeResolved] = []
        skipped: list[SkippedZaak] = []
        for zaak_with_group in raw_result.zaken:
            api_group = zaak_with_group.api_group

            try:
                # Check the rol before resolving anything else, mirroring the order in
                # `check_zaak_access`, so a zaak the user has no claim to never has its
                # metadata resolved. We cannot rely on the API-level
                # `rol__omschrijvingGeneriek` filter here: eSuite is known to ignore
                # filter query params (see Taiga #961 and
                # `ZakenClient.fetch_zaak_roles`).
                with self._report_failure(
                    SkipReason.ROL_RESOLUTION_FAILED, zaak_with_group
                ):
                    has_required_rol = self._user_has_required_rol(
                        zaak_with_group.zaak.url,
                        user_identification,
                        self._zaken_client_factory(api_group, config),
                        use_rsin=api_group.fetch_eherkenning_zaken_with_rsin,
                        limit_access_to_role=limit_access_to_role,
                    )
                if not has_required_rol:
                    continue

                # TODO: could be done in parallel
                catalogi_client = self._catalogi_client_factory(api_group)
                self._resolve_zaak_type(zaak_with_group, catalogi_client)
            except Exception as exc:
                skipped.append(
                    SkippedZaak(
                        zaak_url=zaak_with_group.zaak.url,
                        reasons=frozenset(
                            {self._skip_reason_for(exc, zaak_with_group)}
                        ),
                        api_group=api_group,
                    )
                )
                continue

            if self._is_zaak_visible(zaak_with_group.zaak)[0]:
                visible_zaken.append(
                    ZaakWithApiGroupZaakTypeResolved(
                        zaak=zaak_with_group.zaak,
                        api_group=zaak_with_group.api_group,
                        type_aanvraag=zaak_with_group.type_aanvraag,
                    )
                )

        # A match dropped because the user holds no rol on it, or because it is not
        # visible, is legitimately absent and not reported as skipped. Only failures
        # to resolve are, so that the search page can report incomplete results.
        return ZakenResult(
            zaken=visible_zaken,
            skipped=skipped,
            raw_fetch_incomplete=raw_result.raw_fetch_incomplete,
        )

    def get_visible_zaken(
        self, user_identification: UserIdentification
    ) -> ZakenResult[ZaakWithApiGroupZaakTypeResolved]:
        """
        Fetch all visible zaken with only zaaktype resolved (status/resultaat
        left as raw URLs). This is cheap because zaaktype lookups are cached and
        status presence is checked from raw data. Use this for pagination and
        total-count; pass the page slice to fully_resolve_zaken for display.
        """
        if not user_identification:
            return ZakenResult(zaken=[], skipped=[])

        # Each thread gets its own zaken client because requests.Session is not
        # thread-safe. Pre-fetch OpenZaakConfig to avoid additional DB calls.
        config = OpenZaakConfig.get_solo()
        timeouts = self._case_list_stage_timeouts(config)

        all_api_groups = list(
            ZGWApiGroupConfig.objects.select_related(
                "zrc_service",
                "ztc_service",
                "drc_service",
                "form_service",
            ).all()
        )

        fetched_zaken: list[ZaakWithApiGroup] = []
        raw_fetch_incomplete = False
        with TimedParallel(
            max_workers=self._max_workers, name="get_visible_zaken.raw_fetch"
        ) as executor:
            futures: list[concurrent.futures.Future[list[ZaakWithApiGroup]]] = [
                executor.submit(
                    self._get_raw_zaken_for_api_group,
                    group,
                    user_identification,
                    self._zaken_client_factory(group, config),
                    group.fetch_eherkenning_zaken_with_rsin,
                )
                for group in all_api_groups
            ]
            result = executor.as_completed(
                futures, cancel_after=timeouts["get_raw_zaken"]
            )
            for task in result:
                try:
                    fetched_zaken.extend(task.result())
                except BaseException:
                    logger.exception("Error fetching raw zaken for group")
                    raw_fetch_incomplete = True

        if result.timed_out:
            logger.warning("Timed out fetching raw zaken for group")
            raw_fetch_incomplete = True

        fetched_zaken.sort(
            key=lambda c: (
                # negate ordinal for descending order: date has no __neg__.
                -c.zaak.startdatum.toordinal(),
                all_api_groups.index(c.api_group),
            )
        )

        future_to_zaak: dict[concurrent.futures.Future, ZaakWithApiGroup] = {}
        visible_ids: set[int] = set()
        skipped: list[SkippedZaak] = []
        with TimedParallel(
            max_workers=self._max_workers, name="get_visible_zaken.resolve_zaaktype"
        ) as executor:
            for zaak_with_group in fetched_zaken:
                f = executor.submit(
                    self._resolve_zaak_type,
                    zaak_with_group,
                    self._catalogi_client_factory(zaak_with_group.api_group),
                )
                future_to_zaak[f] = zaak_with_group
            result = executor.as_completed(
                future_to_zaak, cancel_after=timeouts["get_visible_zaken"]
            )
            for future in result:
                zaak_with_group = future_to_zaak[future]
                try:
                    future.result()
                except Exception as exc:
                    # `_skip_reason_for` reports which entity failed to resolve
                    skipped.append(
                        SkippedZaak(
                            zaak_url=zaak_with_group.zaak.url,
                            reasons=frozenset(
                                {self._skip_reason_for(exc, zaak_with_group)}
                            ),
                            api_group=zaak_with_group.api_group,
                        )
                    )
                    continue
                is_visible, skip_reason = self._is_zaak_visible(zaak_with_group.zaak)
                if is_visible:
                    visible_ids.add(id(zaak_with_group))
                else:
                    logger.debug(
                        "Culling zaak %s because it is invisible",
                        zaak_with_group.identification,
                    )
                    skipped.append(
                        SkippedZaak(
                            zaak_url=zaak_with_group.zaak.url,
                            reasons=frozenset({skip_reason}),
                            api_group=zaak_with_group.api_group,
                        )
                    )

        if result.timed_out:
            logger.warning("Timed out resolving zaaktypes")
            skipped.extend(
                SkippedZaak(
                    zaak_url=zaak_with_group.zaak.url,
                    reasons=frozenset({SkipReason.TIMEOUT}),
                    api_group=zaak_with_group.api_group,
                )
                for future, zaak_with_group in future_to_zaak.items()
                if future in result.timed_out_futures
            )

        return ZakenResult(
            zaken=[
                ZaakWithApiGroupZaakTypeResolved(
                    zaak=z.zaak, api_group=z.api_group, type_aanvraag=z.type_aanvraag
                )
                for z in fetched_zaken
                if id(z) in visible_ids
            ],
            skipped=skipped,
            raw_fetch_incomplete=raw_fetch_incomplete,
        )

    def fully_resolve_zaken(
        self, zaken: list[ZaakWithApiGroupZaakTypeResolved]
    ) -> ZakenResult[ZaakWithApiGroupFullyResolved]:
        """
        Fully resolve status+statustype and resultaat+resultaattype
        for a page slice. Input zaken must already have zaaktype resolved
        (as returned by get_visible_zaken). Mutates zaak objects in
        place; zaken that fail resolution are culled from the result.
        The result list is ordered by construction (the input list is
        already ordered).
        """
        future_to_zaak: dict[
            concurrent.futures.Future, ZaakWithApiGroupZaakTypeResolved
        ] = {}
        failure_reasons: dict[int, set[SkipReason]] = defaultdict(set)

        # Each thread gets its own zaken client because requests.Session is not
        # thread-safe. Pre-fetch OpenZaakConfig to avoid additional DB calls.
        config = OpenZaakConfig.get_solo()
        timeouts = self._case_list_stage_timeouts(config)

        with TimedParallel(
            max_workers=self._max_workers, name="fully_resolve_zaken"
        ) as executor:
            for zaak_with_group in zaken:
                group = zaak_with_group.api_group
                f = executor.submit(
                    self._resolve_resultaat_and_resultaat_type,
                    zaak_with_group,
                    self._zaken_client_factory(group, config),
                    self._catalogi_client_factory(group),
                )
                future_to_zaak[f] = zaak_with_group
                if isinstance(zaak_with_group.zaak.status, str):
                    f = executor.submit(
                        self._resolve_status_and_status_type,
                        zaak_with_group,
                        self._zaken_client_factory(group, config),
                        self._catalogi_client_factory(group),
                    )
                    future_to_zaak[f] = zaak_with_group
            result = executor.as_completed(
                future_to_zaak, cancel_after=timeouts["fully_resolve_zaken"]
            )
            for future in result:
                zaak_with_group = future_to_zaak[future]
                try:
                    future.result()
                except Exception as exc:
                    failure_reasons[id(zaak_with_group)].add(
                        self._skip_reason_for(exc, zaak_with_group)
                    )

        if result.timed_out:
            logger.warning("Timed out resolving zaken")
        timed_out_ids = {
            id(future_to_zaak[future]) for future in result.timed_out_futures
        }

        fully_resolved: list[ZaakWithApiGroupFullyResolved] = []
        skipped: list[SkippedZaak] = []
        for zaak_with_group in zaken:
            zid = id(zaak_with_group)
            reasons = set(failure_reasons.get(zid, ()))
            if zid in timed_out_ids:
                # Steps that were still queued (never started) when the stage
                # timed out. Any step that did fail keeps its own reason
                # alongside this one.
                reasons.add(SkipReason.TIMEOUT)
            if reasons:
                skipped.append(
                    SkippedZaak(
                        zaak_url=zaak_with_group.zaak.url,
                        reasons=frozenset(reasons),
                        api_group=zaak_with_group.api_group,
                    )
                )
            else:
                fully_resolved.append(
                    self._replace_catalogus_api_with_model_refs(zaak_with_group)
                )

        return ZakenResult(zaken=fully_resolved, skipped=skipped)

    @staticmethod
    def _fail_resolution(
        reason: SkipReason,
        zaak_with_group: ZaakWithApiGroup,
        cause: BaseException | None = None,
        detail: str = "",
    ) -> NoReturn:
        """Log a resolution failure where it happens and tag it with `reason`.

        Callers of the resolvers only see the `SkipReason`, so the underlying
        error has to be reported here or it is lost.
        """
        logger.error(
            "Failed to resolve ZGW entity for zaak",
            zaak_url=zaak_with_group.zaak.url,
            api_group=str(zaak_with_group.api_group),
            skip_reason=reason.value,
            detail=detail,
            exc_info=cause,
        )
        raise ZaakResolutionError(reason, detail) from cause

    @contextlib.contextmanager
    def _report_failure(
        self, reason: SkipReason, zaak_with_group: ZaakWithApiGroup
    ) -> Iterator[None]:
        """Attribute any failure of a single resolution step to `reason`."""
        try:
            yield
        except Exception as exc:
            self._fail_resolution(reason, zaak_with_group, cause=exc)

    @staticmethod
    def _skip_reason_for(
        exc: BaseException, zaak_with_group: ZaakWithApiGroup
    ) -> SkipReason:
        """Map a failed resolution future to the reason its zaak is skipped.

        The resolvers log and tag their own failures; anything else is unexpected
        and logged here, so that no dropped zaak goes unexplained.
        """
        if isinstance(exc, ZaakResolutionError):
            return exc.reason

        logger.error(
            "Failed to resolve zaak for unexpected reason",
            zaak_url=zaak_with_group.zaak.url,
            api_group=str(zaak_with_group.api_group),
            skip_reason=SkipReason.RESOLUTION_FAILED.value,
            exc_info=exc,
        )
        return SkipReason.RESOLUTION_FAILED

    def _resolve_zaak_type(
        self,
        zaak_with_group: ZaakWithApiGroup,
        catalogi_client: CatalogiClient,
    ) -> None:
        if not isinstance(zaak_with_group.zaak.zaaktype, str):
            logger.debug(
                "Case %s already has a resolved zaaktype",
                zaak_with_group.zaak.identificatie,
            )
            return

        with self._report_failure(
            SkipReason.ZAAKTYPE_RESOLUTION_FAILED, zaak_with_group
        ):
            zaaktype = catalogi_client.fetch_single_zaaktype(
                zaak_with_group.zaak.zaaktype
            )

        with self._zaak_update_lock:
            zaak_with_group.zaak.zaaktype = zaaktype

    def _resolve_status_and_status_type(
        self,
        zaak_with_group: ZaakWithApiGroup,
        zaken_client: ZakenClient,
        catalogi_client: CatalogiClient,
    ) -> None:
        if zaak_with_group.zaak.status is None:
            return

        if not isinstance(zaak_with_group.zaak.status, str):
            self._fail_resolution(
                SkipReason.STATUS_RESOLUTION_FAILED,
                zaak_with_group,
                detail=(
                    f"`case.status` for case {zaak_with_group.zaak.identificatie} "
                    f"is not a str but {type(zaak_with_group.zaak.status)}"
                ),
            )

        with self._report_failure(SkipReason.STATUS_RESOLUTION_FAILED, zaak_with_group):
            status = zaken_client.fetch_single_status(zaak_with_group.zaak.status)

        with self._report_failure(
            SkipReason.STATUSTYPE_RESOLUTION_FAILED, zaak_with_group
        ):
            status_type = catalogi_client.fetch_single_status_type(status.statustype)

        with self._zaak_update_lock:
            zaak_with_group.zaak.status = status
            zaak_with_group.zaak.status.statustype = status_type

    def _resolve_resultaat_and_resultaat_type(
        self,
        zaak_with_group: ZaakWithApiGroup,
        zaken_client: ZakenClient,
        catalogi_client: CatalogiClient,
    ) -> None:
        if zaak_with_group.zaak.resultaat is None:
            return

        if not isinstance(zaak_with_group.zaak.resultaat, str):
            self._fail_resolution(
                SkipReason.RESULTAAT_RESOLUTION_FAILED,
                zaak_with_group,
                detail=(
                    f"`case.resultaat` for case {zaak_with_group.zaak.identificatie} "
                    f"is not a str but {type(zaak_with_group.zaak.resultaat)}"
                ),
            )

        with self._report_failure(
            SkipReason.RESULTAAT_RESOLUTION_FAILED, zaak_with_group
        ):
            resultaat = zaken_client.fetch_single_result(zaak_with_group.zaak.resultaat)

        with self._report_failure(
            SkipReason.RESULTAATTYPE_RESOLUTION_FAILED, zaak_with_group
        ):
            resultaattype = catalogi_client.fetch_single_resultaat_type(
                resultaat.resultaattype
            )

        with self._zaak_update_lock:
            zaak_with_group.zaak.resultaat = resultaat
            zaak_with_group.zaak.resultaat.resultaattype = resultaattype

    def _replace_catalogus_api_with_model_refs(
        self,
        zaak_with_api_group: ZaakWithApiGroupZaakTypeResolved,
    ) -> ZaakWithApiGroupFullyResolved:
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

            if zaak_with_api_group.zaak.status:
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

        return ZaakWithApiGroupFullyResolved(
            zaak=zaak_with_api_group.zaak,
            api_group=zaak_with_api_group.api_group,
            type_aanvraag=zaak_with_api_group.type_aanvraag,
        )

    # -------------------------------------------------------------------------
    # Formulieren
    # -------------------------------------------------------------------------

    def _get_formulieren_for_api_group(
        self,
        group: ZGWApiGroupConfig,
        user_identification: UserIdentification,
        formulieren_client: FormulierenClient,
    ) -> list[FormulierWithApiGroup]:
        return [
            FormulierWithApiGroup(
                formulier=formulier,
                api_group=group,
                type_aanvraag=TypeAanvraag.FORMULIER,
            )
            for formulier in formulieren_client.fetch_formulieren(
                user_identification, use_rsin=group.fetch_eherkenning_zaken_with_rsin
            )
        ]

    def get_formulieren(
        self, user_identification: UserIdentification | None
    ) -> FormulierenResult:
        if not user_identification:
            return FormulierenResult(formulieren=[])

        config = OpenZaakConfig.get_solo()
        timeouts = self._case_list_stage_timeouts(config)

        all_api_groups = list(ZGWApiGroupConfig.objects.with_forms_service())

        subs_with_api_group: list[FormulierWithApiGroup] = []
        with TimedParallel(
            max_workers=self._max_workers, name="get_formulieren"
        ) as executor:
            futures = [
                executor.submit(
                    self._get_formulieren_for_api_group,
                    group,
                    user_identification,
                    self._formulieren_client_factory(group),
                )
                for group in all_api_groups
            ]
            result = executor.as_completed(
                futures, cancel_after=timeouts["get_formulieren"]
            )
            for task in result:
                try:
                    subs_with_api_group.extend(task.result())
                except BaseException:
                    logger.exception("Error fetching and pre-processing formulieren")

        if result.timed_out:
            logger.warning("Timeout while fetching formulieren")

        subs_with_api_group.sort(
            key=lambda sub: sub.formulier.datum_laatste_wijziging, reverse=True
        )

        return FormulierenResult(
            formulieren=subs_with_api_group, timed_out=result.timed_out
        )

    # -------------------------------------------------------------------------
    # Zaak detail
    # -------------------------------------------------------------------------

    def check_zaak_access(
        self,
        zaak_id: str,
        user_identification: UserIdentification,
        api_group: ZGWApiGroupConfig,
    ) -> tuple[Zaak, ZGWApiGroupConfig] | None:
        config = OpenZaakConfig.get_solo()
        zaken_client = self._zaken_client_factory(api_group, config)

        zaak = zaken_client.fetch_single_zaak(zaak_id)

        if not self._user_has_required_rol(
            zaak.url,
            user_identification,
            zaken_client,
            use_rsin=api_group.fetch_eherkenning_zaken_with_rsin,
            limit_access_to_role=config.limit_user_visible_cases_to_role,
        ):
            return None

        catalogi_client = self._catalogi_client_factory(api_group)
        zaak.zaaktype = catalogi_client.fetch_single_zaaktype(zaak.zaaktype)

        if not self._is_zaak_visible(zaak)[0]:
            logger.info("check_zaak_access: zaak not visible", zaak_url=zaak.url)
            return None

        return zaak, api_group

    def get_zaak_by_uuid(self, uuid: str) -> ZaakWithApiGroup | None:
        config = OpenZaakConfig.get_solo()
        api_groups = list(ZGWApiGroupConfig.objects.select_related("zrc_service"))

        def fetch(api_group: ZGWApiGroupConfig) -> ZaakWithApiGroup:
            zaak = self._zaken_client_factory(api_group, config).fetch_single_zaak(uuid)
            return ZaakWithApiGroup(
                zaak=zaak, api_group=api_group, type_aanvraag=TypeAanvraag.ZAAK
            )

        results: list[ZaakWithApiGroup] = []

        with TimedParallel(
            max_workers=self._max_workers, name="get_zaak_by_uuid"
        ) as executor:
            future_to_group: dict[concurrent.futures.Future, ZGWApiGroupConfig] = {
                executor.submit(fetch, group): group for group in api_groups
            }
            result = executor.as_completed(
                future_to_group, cancel_after=config.case_list_fetch_timeout
            )
            for future in result:
                api_group = future_to_group[future]
                try:
                    results.append(future.result())
                except ZgwAPIError as exc:
                    if exc.status_code == 404:
                        continue
                    logger.warning(
                        "error fetching zaak by uuid",
                        uuid=uuid,
                        api_group=api_group.pk,
                        status_code=exc.status_code,
                        exc_info=True,
                    )
                except Exception:
                    logger.warning(
                        "unexpected error fetching zaak by uuid",
                        uuid=uuid,
                        api_group=api_group.pk,
                        exc_info=True,
                    )

        if result.timed_out:
            logger.warning("timed out fetching zaak by uuid", uuid=uuid)

        if len(results) > 1:
            logger.warning(
                "zaak found in multiple API groups",
                uuid=uuid,
                api_groups=[r.api_group.pk for r in results],
            )

        return results[0] if results else None

    def fetch_zaak_by_url(
        self, zaak_url: str, api_group: ZGWApiGroupConfig
    ) -> Zaak | None:
        return self._zaken_client_factory(api_group).fetch_zaak_by_url_no_cache(
            zaak_url
        )

    def fetch_zaak_roles(
        self, zaak_url: str, api_group: ZGWApiGroupConfig
    ) -> list[Rol]:
        client = self._zaken_client_factory(api_group)
        if not client.fetch_rollen_with_betrokkene_type:
            return client.fetch_zaak_roles(zaak_url)
        # Only query types that can map to a user account; medewerker and
        # organisatorische_eenheid are internal government roles and some
        # backends (e.g. iConnect/Decos) reject those types with a 400.
        available_user_betrokkene_types = (
            RolTypes.natuurlijk_persoon,
            RolTypes.niet_natuurlijk_persoon,
            RolTypes.vestiging,
        )
        roles = []
        for betrokkene_type in available_user_betrokkene_types:
            roles += client.fetch_zaak_roles(zaak_url, betrokkene_type=betrokkene_type)
        return roles

    def fetch_zaaktype_by_url(
        self, zaaktype_url: str, api_group: ZGWApiGroupConfig
    ) -> ZaakType | None:
        return self._catalogi_client_factory(api_group).fetch_single_zaaktype(
            zaaktype_url
        )

    def fetch_status_history(
        self, zaak_url: str, api_group: ZGWApiGroupConfig
    ) -> list[Status]:
        client = self._zaken_client_factory(api_group)
        if self._use_cache:
            return client.fetch_status_history(zaak_url)
        return client.fetch_status_history_no_cache(zaak_url)

    def fetch_single_status(
        self, status_url: str, api_group: ZGWApiGroupConfig
    ) -> Status | None:
        return self._zaken_client_factory(api_group).fetch_single_status(status_url)

    def fetch_single_status_type(
        self, status_type_url: str, api_group: ZGWApiGroupConfig
    ) -> StatusType | None:
        return self._catalogi_client_factory(api_group).fetch_single_status_type(
            status_type_url
        )

    def fetch_single_zaak_information_object(
        self, ziobj_url: str, api_group: ZGWApiGroupConfig
    ) -> ZaakInformatieObject | None:
        return self._zaken_client_factory(
            api_group
        ).fetch_single_zaak_information_object(ziobj_url)

    def fetch_single_resultaat_type_for_service(
        self, resultaat_type_url: str, service
    ) -> ResultaatType:
        client = cast(CatalogiClient, build_zgw_client_from_service(service))
        return client.fetch_single_resultaat_type(resultaat_type_url)

    def _sync_statuses_with_status_types(
        self,
        zaak: Zaak,
        statuses: list[Status],
        zaken_client: ZakenClient,
        catalogi_client: CatalogiClient,
    ) -> dict[str, StatusType]:
        """Resolve status URLs to objects. Mutates zaak.status and status.statustype in place.

        Includes eSuite compatibility: when zaak.status URL is absent from the status history,
        fetches it individually (Taiga #2037).
        """
        status_types_mapping: dict = defaultdict(list)

        for status in statuses:
            status_types_mapping[status.statustype].append(status)
            if zaak.status == status.url:
                zaak.status = status

        if isinstance(zaak.status, str):
            logger.info(
                "Issue #2037 -- Retrieving status individually for zaak because of eSuite",
                case_identification=zaak.identification,
            )
            zaak.status = zaken_client.fetch_single_status(zaak.status)
            status_types_mapping[zaak.status.statustype].append(zaak.status)

        for status_type_url, _statuses in list(status_types_mapping.items()):
            status_type = catalogi_client.fetch_single_status_type(status_type_url)
            status_types_mapping[status_type_url] = status_type
            for status in _statuses:
                status.statustype = status_type

        return status_types_mapping

    def _get_initiator_display(
        self,
        zaak: Zaak,
        api_group: ZGWApiGroupConfig,
        user_identification: UserIdentification,
    ) -> str:
        zaken_client = self._zaken_client_factory(api_group)

        if not api_group.fetch_rollen_with_betrokkene_type:
            roles = zaken_client.fetch_zaak_roles(
                zaak.url, role_desc_generic=RolOmschrijving.initiator
            )
        else:
            match user_identification:
                case BSNIdentification():
                    betrokkene_type = RolTypes.natuurlijk_persoon
                case KVKIdentification(vestigingsnummer=str()):
                    betrokkene_type = RolTypes.vestiging
                case KVKIdentification():
                    betrokkene_type = RolTypes.niet_natuurlijk_persoon
                case _:
                    return ""
            roles = zaken_client.fetch_zaak_roles(
                zaak.url,
                betrokkene_type=betrokkene_type,
                role_desc_generic=RolOmschrijving.initiator,
            )

        return ", ".join(get_role_name_display(r) for r in roles)

    def get_zaak_detail(
        self,
        zaak: Zaak,
        api_group: ZGWApiGroupConfig,
        user_identification: UserIdentification,
    ) -> ZaakDetailData:
        """Fetch and resolve all ZGW API data for the zaak detail page.

        Mutates zaak.status (URL → Status) and each status.statustype (URL -> StatusType).
        """
        zaken_client = self._zaken_client_factory(api_group)
        catalogi_client = self._catalogi_client_factory(api_group)
        openzaak_config = OpenZaakConfig.get_solo()

        statuses = zaken_client.fetch_status_history(zaak.url)
        statustypen = catalogi_client.fetch_statustypes_no_cache(zaak.zaaktype.url)

        if openzaak_config.order_statuses_by_date_set:
            statuses.sort(key=lambda s: s.datum_status_gezet)
        else:
            statuses.reverse()

        status_types_mapping = self._sync_statuses_with_status_types(
            zaak, statuses, zaken_client, catalogi_client
        )

        documents = self._fetch_zaak_documents(zaak, api_group)
        initiator = self._get_initiator_display(zaak, api_group, user_identification)

        result: dict = {}
        if zaak.resultaat:
            result_obj = zaken_client.fetch_single_result(zaak.resultaat)
            result_type = catalogi_client.fetch_single_resultaat_type(
                result_obj.resultaattype
            )
            result_type_config_mapping = {
                zt_result.resultaattype_url: zt_result
                for zt_result in ZaakTypeResultaatTypeConfig.objects.filter(
                    zaaktype_config__identificatie=zaak.zaaktype.identificatie
                )
            }
            result = {
                "display": result_obj.toelichting,
                "description": getattr(result_type, "esuite_compat_naam", "")
                or getattr(
                    result_type_config_mapping.get(result_obj.resultaattype),
                    "description",
                    "",
                ),
            }

        return ZaakDetailData(
            statuses=statuses,
            statustypen=statustypen,
            status_types_mapping=status_types_mapping,
            documents=documents,
            result=result,
            initiator=initiator,
        )

    # -------------------------------------------------------------------------
    # Documenten
    # -------------------------------------------------------------------------

    def _fetch_zaak_documents(
        self,
        zaak: Zaak,
        api_group: ZGWApiGroupConfig,
    ) -> list[ZaakDocumentData]:
        """Fetch zaak documents filtered by visibility. Sorted newest-first."""
        case_info_objects = self._zaken_client_factory(
            api_group
        ).fetch_zaak_information_objects(zaak.url)

        config = OpenZaakConfig.get_solo()
        documents = []
        for case_info_obj in case_info_objects:
            try:
                info_obj = self.fetch_information_object_by_url(
                    case_info_obj.informatieobject, api_group
                )
            except ZgwAPIError:
                logger.error(
                    "Failed to fetch document info object",
                    informatieobject_url=case_info_obj.informatieobject,
                )
                continue
            if not self._is_info_object_visible(
                info_obj,
                config.document_max_confidentiality,
                config.document_visible_statuses,
            ):
                continue
            documents.append(
                ZaakDocumentData(case_info_obj=case_info_obj, info_obj=info_obj)
            )

        try:
            return sorted(
                documents,
                key=lambda d: d.case_info_obj.registratiedatum,
                reverse=True,
            )
        except TypeError:
            try:
                return sorted(documents, key=lambda d: d.info_obj.titel)
            except TypeError:
                return documents

    def fetch_information_object_by_url(
        self, url: str, api_group: ZGWApiGroupConfig
    ) -> InformatieObject:
        return self._documenten_client_factory(
            api_group
        )._fetch_single_information_object(url=url)

    def fetch_information_object_by_uuid(
        self, uuid: str, api_group: ZGWApiGroupConfig
    ) -> InformatieObject:
        return self._documenten_client_factory(
            api_group
        )._fetch_single_information_object(uuid=uuid)

    def fetch_zaak_information_objects_for_zaak_and_info(
        self, zaak_url: str, info_object_url: str, api_group: ZGWApiGroupConfig
    ) -> list:
        return self._zaken_client_factory(
            api_group
        ).fetch_zaak_information_objects_for_zaak_and_info(zaak_url, info_object_url)

    def download_document(self, url: str, api_group: ZGWApiGroupConfig):
        return self._documenten_client_factory(api_group).download_document(url)

    def upload_document(
        self,
        user,
        file,
        title: str,
        informatieobjecttype_url: str,
        source_organization: str,
        api_group: ZGWApiGroupConfig,
    ) -> dict:
        return self._documenten_client_factory(api_group).upload_document(
            user, file, title, informatieobjecttype_url, source_organization
        )

    def connect_case_with_document(
        self, zaak_url: str, document_url: str, api_group: ZGWApiGroupConfig
    ) -> dict:
        return self._zaken_client_factory(api_group).connect_case_with_document(
            zaak_url, document_url
        )

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    def fetch_open_tasks(self, bsn: str) -> list[OpenstaandeTaak]:
        all_api_groups = list(ZGWApiGroupConfig.objects.with_forms_service())
        tasks = []
        for group in all_api_groups:
            try:
                client = self._formulieren_client_factory(group)
                tasks.extend(client.fetch_open_tasks(bsn=bsn))
            except ZgwAPIError:
                logger.exception(
                    "Error fetching open tasks from ZGW API", api_group=str(group)
                )
        return tasks
