from __future__ import annotations

import concurrent.futures
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import TypedDict, cast

from django.conf import settings

import structlog
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes
from zgw_consumers.concurrent import parallel

from open_inwoner.openzaak.api_models import (
    Formulier,
    InformatieObject,
    Rol,
    Status,
    StatusType,
    Zaak,
    ZaakInformatieObject,
    ZaakType,
)
from open_inwoner.openzaak.clients import (
    CatalogiClient,
    ZakenClient,
    build_zgw_client_from_service,
)
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.documents import fetch_single_information_object_from_url
from open_inwoner.openzaak.identity import BSNIdentity, KVKIdentity, UserIdentity
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
)
from open_inwoner.openzaak.utils import (
    get_role_name_display,
    is_info_object_visible,
    is_object_visible,
)

logger = structlog.stdlib.get_logger(__name__)


class ResolveCaseException(Exception):
    pass


# TODO: temporary workaround for our practice of swalling exceptions into None
# at the client layer. Should be removed when the refactoring of error-handling
# is completed (see GH #2142)
class ZaakNotFound(Exception):
    """Raised by check_zaak_access when the zaak cannot be fetched (API error or 404)."""

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
    fetch_raw_zaken: int | float
    resolve_zaken: int | float
    fetch_formulieren: int | float


class ZGWService:
    _max_workers: int
    _timeouts: Timeouts

    def __init__(self, use_cache: bool = True):
        self._use_cache = use_cache
        self._timeouts = {
            "fetch_raw_zaken": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.3,
            "resolve_zaken": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.5,
            "fetch_formulieren": settings.ZGW_CASE_LIST_FETCH_TIMEOUT * 0.2,
        }
        self._max_workers = settings.ZGW_CASE_LIST_NUM_WORKERS
        # Resolvers mutate Zaak fields in parallel futures; the lock prevents concurrent writes.
        self._zaak_update_lock = threading.RLock()

        logger.debug(
            "Configured ZGWService",
            timeouts=self._timeouts,
            max_workers=self._max_workers,
        )

    @staticmethod
    def _zaken_client_factory(group: ZGWApiGroupConfig) -> ZakenClient:
        return cast(
            ZakenClient,
            build_zgw_client_from_service(
                group.zrc_service,
                use_openzaak_120_params=group.fetch_eherkenning_zaken_with_openzaak_120_params,
                fetch_rollen_with_betrokkene_type=group.fetch_rollen_with_betrokkene_type,
            ),
        )

    @staticmethod
    def _catalogi_client_factory(group: ZGWApiGroupConfig) -> CatalogiClient:
        return cast(CatalogiClient, build_zgw_client_from_service(group.ztc_service))

    @staticmethod
    def _is_zaak_visible(zaak: Zaak) -> bool:
        config = OpenZaakConfig.get_solo()
        if isinstance(zaak.zaaktype, str):
            raise ValueError("expected zaak.zaaktype to be resolved from url to model")
        if not zaak.status and not config.show_cases_without_status:
            logger.info(
                "Ignoring zaak as not visible for users: zaak has no status and show_cases_without_status is disabled",
                zaak_url=zaak.url,
            )
            return False
        if not zaak.zaaktype:
            logger.info(
                "Ignoring zaak as not visible for users: zaak has no zaaktype",
                zaak_url=zaak.url,
            )
            return False
        if zaak.zaaktype.indicatie_intern_of_extern != "extern":
            logger.info(
                "Ignoring zaak as not visible for users: zaaktype is intern",
                zaak_url=zaak.url,
            )
            return False
        return is_object_visible(zaak, config.zaak_max_confidentiality)

    def _get_formulieren_for_api_group(
        self, group: ZGWApiGroupConfig, user_identity: UserIdentity
    ) -> list[FormulierWithApiGroup]:
        if not group.forms_client:
            raise ValueError(f"{group} has no `forms_client`")

        return [
            FormulierWithApiGroup(
                formulier=formulier,
                api_group=group,
                type_aanvraag=TypeAanvraag.FORMULIER,
            )
            for formulier in group.forms_client.fetch_formulieren(
                user_identity, use_rsin=group.fetch_eherkenning_zaken_with_rsin
            )
        ]

    def get_formulieren(
        self, user_identity: UserIdentity | None
    ) -> list[FormulierWithApiGroup]:
        if not user_identity:
            return []

        all_api_groups = list(
            ZGWApiGroupConfig.objects.filter(form_service__isnull=False).select_related(
                "form_service",
            )
        )

        subs_with_api_group: list[FormulierWithApiGroup] = []
        with parallel(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(
                    self._get_formulieren_for_api_group, group, user_identity
                )
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
                    logger.exception("Error fetching and pre-processing formulieren")
        except concurrent.futures.TimeoutError:
            logger.warning("Timeout while fetching formulieren")

        subs_with_api_group.sort(
            key=lambda sub: sub.formulier.datum_laatste_wijziging, reverse=True
        )

        return subs_with_api_group

    def fetch_zaak_by_url(
        self, zaak_url: str, api_group: ZGWApiGroupConfig
    ) -> Zaak | None:
        return self._zaken_client_factory(api_group).fetch_zaak_by_url_no_cache(
            zaak_url
        )

    def fetch_status_history(
        self, zaak_url: str, api_group: ZGWApiGroupConfig
    ) -> list[Status]:
        client = self._zaken_client_factory(api_group)
        if self._use_cache:
            return client.fetch_status_history(zaak_url)
        return client.fetch_status_history_no_cache(zaak_url)

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

    def fetch_single_zaak_information_object(
        self, ziobj_url: str, api_group: ZGWApiGroupConfig
    ) -> ZaakInformatieObject | None:
        return self._zaken_client_factory(
            api_group
        ).fetch_single_zaak_information_object(ziobj_url)

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

    def check_zaak_access(
        self,
        zaak_id: str,
        user_identity: UserIdentity,
        api_group: ZGWApiGroupConfig,
    ) -> tuple[Zaak, ZGWApiGroupConfig] | None:
        zaken_client = self._zaken_client_factory(api_group)

        zaak = zaken_client.fetch_single_zaak(zaak_id)
        # TODO: temporary workaround for our practice of swalling exceptions into None
        # at the client layer. Should be removed when the refactoring of error-handling
        # is completed (see GH #2142)
        if not zaak:
            raise ZaakNotFound(f"Zaak {zaak_id!r} not found or API unavailable")

        config = OpenZaakConfig.get_solo()
        limit_access_to_role = config.limit_user_visible_cases_to_role

        rollen = zaken_client.fetch_rollen_for_user(
            zaak.url,
            user_identity,
            use_rsin=api_group.fetch_eherkenning_zaken_with_rsin,
        )

        if not rollen:
            logger.info("check_zaak_access: no role for zaak", zaak_url=zaak.url)
            return None

        if limit_access_to_role and not any(
            rol.omschrijving_generiek == limit_access_to_role for rol in rollen
        ):
            logger.info(
                "check_zaak_access: incorrect role for zaak",
                zaak_url=zaak.url,
                required_role=limit_access_to_role,
            )
            return None

        catalogi_client = self._catalogi_client_factory(api_group)
        zaak.zaaktype = catalogi_client.fetch_single_zaaktype(zaak.zaaktype)
        if not zaak.zaaktype:
            logger.info("check_zaak_access: no zaaktype for zaak", zaak_url=zaak.url)
            return None

        if not self._is_zaak_visible(zaak):
            logger.info("check_zaak_access: zaak not visible", zaak_url=zaak.url)
            return None

        return zaak, api_group

    def _get_raw_zaken_for_api_group(
        self,
        group: ZGWApiGroupConfig,
        user_identity: UserIdentity,
        zaak_identificatie: str | None = None,
    ) -> list[ZaakWithApiGroup]:
        raw_zaken = group.zaken_client.fetch_zaken(
            user_identity,
            use_rsin=group.fetch_eherkenning_zaken_with_rsin,
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
        user_identity: UserIdentity,
        zaak_identificatie: str | None = None,
    ) -> list[ZaakWithApiGroup]:
        """Fetch zaken without resolution. For PDC and cache seeding."""
        all_api_groups = list(
            ZGWApiGroupConfig.objects.select_related("zrc_service").all()
        )

        fetched_zaken: list[ZaakWithApiGroup] = []
        with parallel(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(
                    self._get_raw_zaken_for_api_group,
                    group,
                    user_identity,
                    zaak_identificatie,
                )
                for group in all_api_groups
            ]

        try:
            for task in concurrent.futures.as_completed(
                futures,
                timeout=self._timeouts["fetch_raw_zaken"],
            ):
                try:
                    fetched_zaken.extend(task.result())
                except BaseException:
                    logger.exception("Error fetching raw zaken for group")
        except concurrent.futures.TimeoutError:
            logger.warning("Timed out fetching raw zaken", exc_info=True)

        return fetched_zaken

    def search_zaken(
        self, user_identity: UserIdentity, zaak_identificatie: str
    ) -> list[ZaakWithApiGroup]:
        """Search for a zaak by zaak_identificatie across all API groups. Returns visible matches."""
        visible_zaken = []
        for zaak_with_group in self.get_raw_zaken(user_identity, zaak_identificatie):
            try:
                # TODO: could be done in parallel
                self._resolve_zaak_type(zaak_with_group)
            except ResolveCaseException:
                logger.warning(
                    "Unable to resolve zaaktype for search result",
                    zaak_url=zaak_with_group.zaak.url,
                )
                continue
            if self._is_zaak_visible(zaak_with_group.zaak):
                visible_zaken.append(zaak_with_group)

        return visible_zaken

    def get_zaken(self, user_identity: UserIdentity) -> list[ZaakWithApiGroup]:
        if not user_identity:
            return []

        all_api_groups = list(
            ZGWApiGroupConfig.objects.select_related(
                "zrc_service",
                "ztc_service",
                "drc_service",
                "form_service",
            ).all()
        )

        fetched_zaken: list[ZaakWithApiGroup] = []
        fetch_raw_zaken_futures: list[
            concurrent.futures.Future[list[ZaakWithApiGroup]]
        ] = []
        with parallel(max_workers=self._max_workers) as executor:
            fetch_raw_zaken_futures.extend(
                executor.submit(self._get_raw_zaken_for_api_group, group, user_identity)
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
            logger.warning("Timed out fetching raw zaken for group", exc_info=True)
        except BaseException:
            logger.exception("Unhandled error fetching raw zaken")

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
                for func in resolver_functions:
                    future = executor.submit(func, zaak_with_group)
                    all_futures.append(future)
                    zaak_futures[zaak_with_group].append(future)

        try:
            concurrent.futures.wait(
                all_futures,
                timeout=self._timeouts["resolve_zaken"],
            )
        except concurrent.futures.TimeoutError:
            logger.warning("Timed out resolving zaken", exc_info=True)
        except BaseException:
            logger.exception("Unhandled error during zaak resolution")

        resolved_zaken: list[ZaakWithApiGroup] = []
        for zaak, futures in zaak_futures.items():
            if not all(f.done() and not f.exception() for f in futures):
                logger.warning(
                    "Culling zaak %s because not all resolutions completed successfully",
                    zaak.identification,
                )
                continue

            zaak_with_resolved_zgw_refs = self._replace_catalogus_api_with_model_refs(
                zaak
            )

            if self._is_zaak_visible(zaak_with_resolved_zgw_refs.zaak):
                resolved_zaken.append(zaak_with_resolved_zgw_refs)
            else:
                logger.debug(
                    "Culling zaak %s because it is invisible",
                    zaak_with_resolved_zgw_refs.identification,
                )

        resolved_zaken.sort(
            key=lambda c: (
                -c.zaak.startdatum.toordinal(),
                all_api_groups.index(c.api_group),
            )
        )
        return resolved_zaken

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

    def _resolve_zaak_type(self, zaak_with_group: ZaakWithApiGroup) -> None:
        client = ZGWService._catalogi_client_factory(zaak_with_group.api_group)
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
        self, zaak_with_group: ZaakWithApiGroup
    ) -> None:
        zaken_client = ZGWService._zaken_client_factory(zaak_with_group.api_group)
        catalogi_client = ZGWService._catalogi_client_factory(zaak_with_group.api_group)

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
        self, zaak_with_group: ZaakWithApiGroup
    ) -> None:
        if zaak_with_group.zaak.resultaat is None:
            return

        zaken_client = ZGWService._zaken_client_factory(zaak_with_group.api_group)
        catalogi_client = ZGWService._catalogi_client_factory(zaak_with_group.api_group)

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

    def _fetch_zaak_documents(
        self,
        zaak: Zaak,
        api_group: ZGWApiGroupConfig,
    ) -> list[ZaakDocumentData]:
        """Fetch zaak documents filtered by visibility. Sorted newest-first."""
        case_info_objects = api_group.zaken_client.fetch_zaak_information_objects(
            zaak.url
        )
        info_objects = [
            fetch_single_information_object_from_url(
                case_info.informatieobject, api_group=api_group
            )
            for case_info in case_info_objects
        ]

        config = OpenZaakConfig.get_solo()
        documents = []
        for case_info_obj, info_obj in zip(case_info_objects, info_objects):
            if not info_obj:
                continue
            if not is_info_object_visible(
                info_obj, config.document_max_confidentiality
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

    def _get_initiator_display(
        self,
        zaak: Zaak,
        api_group: ZGWApiGroupConfig,
        user_identity: UserIdentity,
    ) -> str:
        zaken_client = api_group.zaken_client

        if not api_group.fetch_rollen_with_betrokkene_type:
            roles = zaken_client.fetch_zaak_roles(
                zaak.url, role_desc_generic=RolOmschrijving.initiator
            )
        else:
            match user_identity:
                case BSNIdentity():
                    betrokkene_type = RolTypes.natuurlijk_persoon
                case KVKIdentity(vestigingsnummer=str()):
                    betrokkene_type = RolTypes.vestiging
                case KVKIdentity():
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
        user_identity: UserIdentity,
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
        initiator = self._get_initiator_display(zaak, api_group, user_identity)

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
