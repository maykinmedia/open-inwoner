from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from textwrap import dedent
from typing import Literal

from django.utils.translation import gettext as _

import structlog
from jinja2 import Template

from open_inwoner.openzaak.models import (
    CatalogusConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
)

logger = structlog.stdlib.get_logger(__name__)


class ExclusionReason(StrEnum):
    """Reasons why an object was excluded from import"""

    FILTERED_INTERNAL = _("Object uitgefilterd omdat deze als 'intern' is aangemerkt")
    API_ERROR = _(
        "Object uitgefilterd omdat deze door een API fout niet kon worden opgevraagd"
    )
    DATABASE_ERROR = _(
        "Object uitgefilterd omdat deze door een database fout niet kon worden opgeslagen"
    )
    MISSING_CATALOGUS = _("Object verwijst naar een niet-bestaande catalogus")
    NO_CLIENT = _("Object uitgefilterd omdat er geen valide client beschikbaar was")


@dataclass
class ExcludedObject:
    """Represents an object that was excluded from import"""

    object_type: Literal[
        "Catalogus",
        "ZaakType",
        "InformatieObjectType",
        "StatusType",
        "ResultaatType",
    ]
    url: str
    identificatie: str = ""
    reason: ExclusionReason = ExclusionReason.API_ERROR
    error_message: str = ""
    extra_context: dict = field(default_factory=dict)


@dataclass
class ImportResult[T]:
    """Generic result class for tracking what was synced"""

    created: list[T] = field(default_factory=list)
    updated: list[T] = field(default_factory=list)
    excluded: list[ExcludedObject] = field(default_factory=list)
    not_found_in_api: list[T] = field(default_factory=list)

    @property
    def total_synced(self) -> int:
        return len(self.created) + len(self.updated)

    @property
    def total_excluded(self) -> int:
        return len(self.excluded)

    @property
    def total_not_found_in_api(self) -> int:
        return len(self.not_found_in_api)


@dataclass
class ZaakTypeRelatedImportResult[T]:
    """Result of importing related types for a specific zaaktype"""

    zaaktype_config: ZaakTypeConfig | None = None
    created: list[T] = field(default_factory=list)
    updated: list[T] = field(default_factory=list)
    excluded: list[ExcludedObject] = field(default_factory=list)
    not_found_in_api: list[T] = field(default_factory=list)

    @property
    def total_synced(self) -> int:
        return len(self.created) + len(self.updated)

    @property
    def total_excluded(self) -> int:
        return len(self.excluded)

    @property
    def total_not_found_in_api(self) -> int:
        return len(self.not_found_in_api)


@dataclass
class FullImportResult:
    """Complete result of full import operation"""

    api_group: ZGWApiGroupConfig
    catalogi: ImportResult[CatalogusConfig] = field(
        default_factory=lambda: ImportResult[CatalogusConfig]()
    )
    zaaktypen: ImportResult[ZaakTypeConfig] = field(
        default_factory=lambda: ImportResult[ZaakTypeConfig]()
    )
    informatieobjecttypen: list[
        ZaakTypeRelatedImportResult[ZaakTypeInformatieObjectTypeConfig]
    ] = field(default_factory=list)
    statustypen: list[ZaakTypeRelatedImportResult[ZaakTypeStatusTypeConfig]] = field(
        default_factory=list
    )
    resultaattypen: list[ZaakTypeRelatedImportResult[ZaakTypeResultaatTypeConfig]] = (
        field(default_factory=list)
    )

    def pretty_print(self) -> str:
        """
        Generate a human-readable summary of the import results.

        Returns:
            Formatted string showing created, updated, and excluded objects by category
        """
        section_template = Template(
            dedent("""
            {{ emoji }} {{ title }}
            --------------------------------------------------------------------------------
            {%- if created_items %}
              ✨ Created ({{ created_items|length }}):
            {%- for item in created_items %}
                 - {{ item }}
            {%- endfor %}
            {%- endif %}
            {%- if updated_items %}
              🔄 Updated ({{ updated_items|length }}):
            {%- for item in updated_items %}
                 - {{ item }}
            {%- endfor %}
            {%- endif %}
            {%- if excluded_items %}
              ⚠️  Excluded ({{ excluded_items|length }}):
            {%- for exc_item in excluded_items %}
                 - {{ exc_item.label }}
                   Reason: {{ exc_item.reason }}
            {%- if exc_item.error %}
                   🔴 Error: {{ exc_item.error }}
            {%- endif %}
            {%- endfor %}
            {%- endif %}
            {%- if not_found_items %}
              🔍 Not Found in API ({{ not_found_items|length }}):
            {%- for item in not_found_items %}
                 - {{ item }}
            {%- endfor %}
            {%- endif %}
            {%- if not created_items and not updated_items and not excluded_items and not not_found_items %}
              No changes
            {%- endif %}
        """).strip()
        )

        # Prepare sections data
        sections = []

        # Catalogus section
        cat_created = [
            f"{cat.domein} (RSIN: {cat.rsin or 'N/A'})" for cat in self.catalogi.created
        ]
        cat_updated = [
            f"{cat.domein} (RSIN: {cat.rsin or 'N/A'})" for cat in self.catalogi.updated
        ]
        cat_excluded = [
            {
                "label": "Catalogus",
                "reason": exc.reason.value,
                "error": exc.error_message,
            }
            for exc in self.catalogi.excluded
        ]
        cat_not_found = [
            f"{cat.domein} (RSIN: {cat.rsin or 'N/A'})"
            for cat in self.catalogi.not_found_in_api
        ]
        sections.append(
            {
                "emoji": "📂",
                "title": "Catalogus Configs",
                "created_items": sorted(cat_created),
                "updated_items": sorted(cat_updated),
                "excluded_items": sorted(cat_excluded, key=lambda x: x["label"]),
                "not_found_items": sorted(cat_not_found),
            }
        )

        # ZaakType section
        zt_created = [
            f"{zt.identificatie}: {zt.omschrijving}" for zt in self.zaaktypen.created
        ]
        zt_updated = [
            f"{zt.identificatie}: {zt.omschrijving}" for zt in self.zaaktypen.updated
        ]
        zt_excluded = [
            {
                "label": f"{exc.identificatie or 'Unknown'}: {exc.extra_context.get('omschrijving', '')}",
                "reason": exc.reason.value,
                "error": exc.error_message,
            }
            for exc in self.zaaktypen.excluded
        ]
        zt_not_found = [
            f"{zt.identificatie}: {zt.omschrijving}"
            for zt in self.zaaktypen.not_found_in_api
        ]
        sections.append(
            {
                "emoji": "📋",
                "title": "ZaakType Configs",
                "created_items": sorted(zt_created),
                "updated_items": sorted(zt_updated),
                "excluded_items": sorted(zt_excluded, key=lambda x: x["label"]),
                "not_found_items": sorted(zt_not_found),
            }
        )

        # InformatieObjectType section
        iot_created = []
        iot_updated = []
        iot_excluded = []
        iot_not_found = []
        for result in self.informatieobjecttypen:
            zt_id = (
                result.zaaktype_config.identificatie
                if result.zaaktype_config
                else "Unknown"
            )
            iot_created.extend(
                [f"{item.omschrijving} (ZaakType: {zt_id})" for item in result.created]
            )
            iot_updated.extend(
                [f"{item.omschrijving} (ZaakType: {zt_id})" for item in result.updated]
            )
            iot_excluded.extend(
                [
                    {
                        "label": f"ZaakType: {zt_id}",
                        "reason": exc.reason.value,
                        "error": exc.error_message,
                    }
                    for exc in result.excluded
                ]
            )
            iot_not_found.extend(
                [
                    f"{item.omschrijving} (ZaakType: {zt_id})"
                    for item in result.not_found_in_api
                ]
            )

        sections.append(
            {
                "emoji": "📄",
                "title": "InformatieObjectType Configs",
                "created_items": sorted(iot_created),
                "updated_items": sorted(iot_updated),
                "excluded_items": sorted(iot_excluded, key=lambda x: x["label"]),
                "not_found_items": sorted(iot_not_found),
            }
        )

        # StatusType section
        st_created = []
        st_updated = []
        st_excluded = []
        st_not_found = []
        for result in self.statustypen:
            zt_id = (
                result.zaaktype_config.identificatie
                if result.zaaktype_config
                else "Unknown"
            )
            st_created.extend(
                [f"{item.omschrijving} (ZaakType: {zt_id})" for item in result.created]
            )
            st_updated.extend(
                [f"{item.omschrijving} (ZaakType: {zt_id})" for item in result.updated]
            )
            st_excluded.extend(
                [
                    {
                        "label": f"ZaakType: {zt_id}",
                        "reason": exc.reason.value,
                        "error": exc.error_message,
                    }
                    for exc in result.excluded
                ]
            )
            st_not_found.extend(
                [
                    f"{item.omschrijving} (ZaakType: {zt_id})"
                    for item in result.not_found_in_api
                ]
            )

        sections.append(
            {
                "emoji": "🔔",
                "title": "StatusType Configs",
                "created_items": sorted(st_created),
                "updated_items": sorted(st_updated),
                "excluded_items": sorted(st_excluded, key=lambda x: x["label"]),
                "not_found_items": sorted(st_not_found),
            }
        )

        # ResultaatType section
        rt_created = []
        rt_updated = []
        rt_excluded = []
        rt_not_found = []
        for result in self.resultaattypen:
            zt_id = (
                result.zaaktype_config.identificatie
                if result.zaaktype_config
                else "Unknown"
            )
            rt_created.extend(
                [f"{item.omschrijving} (ZaakType: {zt_id})" for item in result.created]
            )
            rt_updated.extend(
                [f"{item.omschrijving} (ZaakType: {zt_id})" for item in result.updated]
            )
            rt_excluded.extend(
                [
                    {
                        "label": f"ZaakType: {zt_id}",
                        "reason": exc.reason.value,
                        "error": exc.error_message,
                    }
                    for exc in result.excluded
                ]
            )
            rt_not_found.extend(
                [
                    f"{item.omschrijving} (ZaakType: {zt_id})"
                    for item in result.not_found_in_api
                ]
            )

        sections.append(
            {
                "emoji": "✅",
                "title": "ResultaatType Configs",
                "created_items": sorted(rt_created),
                "updated_items": sorted(rt_updated),
                "excluded_items": sorted(rt_excluded, key=lambda x: x["label"]),
                "not_found_items": sorted(rt_not_found),
            }
        )

        # Calculate totals
        total_created = sum(len(s["created_items"]) for s in sections)
        total_updated = sum(len(s["updated_items"]) for s in sections)
        total_excluded = sum(len(s["excluded_items"]) for s in sections)
        total_not_found = sum(len(s["not_found_items"]) for s in sections)

        # Build output
        output_parts = [
            "=" * 80,
            f"ZGW Import Results for {self.api_group}",
            "=" * 80,
            "",
        ]

        # Render each section
        output_parts.extend(section_template.render(**section) for section in sections)

        # Add summary
        output_parts.extend(
            [
                "",
                "=" * 80,
                "Summary",
                "=" * 80,
                f"Total Created:  {total_created}",
                f"Total Updated:  {total_updated}",
                f"Total Excluded: {total_excluded}",
                f"Total Not Found: {total_not_found}",
                "=" * 80,
            ]
        )

        return "\n".join(output_parts)


_CACHE_MISS = object()


class ZGWCatalogusImporter:
    """
    Handles importing ZGW Catalogus configuration objects.

    This class consolidates the logic for importing catalogi, zaaktypen, and related
    objects from a ZGW API backend. It tracks what was synced and what was excluded.
    """

    def __init__(self, zgw_api_group: ZGWApiGroupConfig):
        """
        Initialize the importer with a specific ZGW API group.

        Args:
            zgw_api_group: The ZGW API group configuration to use for imports
        """
        self.zgw_api_group = zgw_api_group
        self.catalogi_client = zgw_api_group.catalogi_client

    def import_all(self) -> FullImportResult:
        """
        Import all catalogus data: catalogi, zaaktypen, and related types.

        Returns:
            FullImportResult with details on what was synced and excluded
        """
        result = FullImportResult(api_group=self.zgw_api_group)

        # Import catalogi
        result.catalogi = self.import_catalogus_configs()

        # Import zaaktypen
        result.zaaktypen = self.import_zaaktype_configs()

        # Import related types for each zaaktype
        for ztc in ZaakTypeConfig.objects.filter(
            catalogus__service=self.zgw_api_group.ztc_service
        ).order_by("catalogus__domein", "identificatie"):
            result.informatieobjecttypen.append(
                self.import_informatieobjecttype_configs_for_zaaktype(ztc)
            )
            result.statustypen.append(self.import_statustype_configs_for_zaaktype(ztc))
            result.resultaattypen.append(
                self.import_resultaattype_configs_for_zaaktype(ztc)
            )

        return result

    def import_catalogus_configs(self) -> ImportResult[CatalogusConfig]:
        """
        Import catalogus configurations from the ZGW API.

        Returns:
            ImportResult with created/updated/excluded catalogi
        """
        result = ImportResult[CatalogusConfig]()

        try:
            catalogi = self.catalogi_client.fetch_catalogs_no_cache()
        except Exception as exc:
            logger.exception(
                "Failed to fetch catalogi from ZGW API",
                client=self.catalogi_client,
            )
            result.excluded.append(
                ExcludedObject(
                    object_type="Catalogus",
                    url=self.catalogi_client.configured_from.api_root,
                    reason=ExclusionReason.API_ERROR,
                    error_message=str(exc),
                )
            )
            return result

        if not catalogi:
            return result

        # Get existing catalogus configs by URL (url is globally unique).
        # We query all configs regardless of service because:
        # 1. The url field has a global unique constraint
        # 2. A catalogus might have been imported from a different service previously
        # 3. We intentionally update the service field to take ownership (see below)
        # This prevents UniqueViolation errors when a catalogus switches services.
        catalogus_urls = [c.url for c in catalogi]
        existing_configs = {
            config.url: config
            for config in CatalogusConfig.objects.filter(url__in=catalogus_urls)
        }

        # Also get configs from current service not in this import (for orphan detection).
        # We only mark configs as orphaned if they belong to the current service,
        # preventing Service A from marking Service B's catalogus as orphaned.
        existing_service_configs = {
            config.url: config
            for config in CatalogusConfig.objects.filter(
                service=self.catalogi_client.configured_from
            )
        }

        catalogus_urls_seen = set()
        for catalogus in catalogi:
            catalogus_urls_seen.add(catalogus.url)
            if existing := existing_configs.get(catalogus.url):
                # Update existing
                updated = False

                # Update all fields that overlap with API model
                if existing.service != self.catalogi_client.configured_from:
                    existing.service = self.catalogi_client.configured_from
                    updated = True

                if existing.rsin != (catalogus.rsin or ""):
                    existing.rsin = catalogus.rsin or ""
                    updated = True

                if existing.domein != catalogus.domein:
                    existing.domein = catalogus.domein
                    updated = True

                # Mark as found in API
                if not existing.found_in_api:
                    existing.found_in_api = True
                    updated = True

                if updated:
                    try:
                        existing.save()
                        result.updated.append(existing)
                    except Exception as exc:
                        logger.exception(
                            "Failed to update catalogus config",
                            url=catalogus.url,
                        )
                        result.excluded.append(
                            ExcludedObject(
                                object_type="Catalogus",
                                url=catalogus.url,
                                reason=ExclusionReason.DATABASE_ERROR,
                                error_message=f"Save failed: {exc}",
                            )
                        )
            else:
                # Create new
                new_config = CatalogusConfig(
                    url=catalogus.url,
                    rsin=catalogus.rsin or "",
                    domein=catalogus.domein,
                    service=self.catalogi_client.configured_from,
                    found_in_api=True,
                )
                try:
                    new_config.save()
                    result.created.append(new_config)
                    existing_configs[catalogus.url] = new_config
                except Exception as exc:
                    logger.exception(
                        "Failed to create catalogus config",
                        url=catalogus.url,
                    )
                    result.excluded.append(
                        ExcludedObject(
                            object_type="Catalogus",
                            url=catalogus.url,
                            reason=ExclusionReason.DATABASE_ERROR,
                            error_message=f"Save failed: {exc}",
                        )
                    )

        # Handle CatalogusConfig objects that were not seen in the API response
        # Only check configs that belong to the current service being imported
        not_found_configs = []
        for config_url, config in existing_service_configs.items():
            if config_url not in catalogus_urls_seen:
                # This catalogus no longer exists in the API for this service
                logger.info(
                    "Catalogus config exists in database but not found in API",
                    url=config_url,
                    service=config.service,
                )
                not_found_configs.append(config)
                result.not_found_in_api.append(config)

        if not_found_configs:
            CatalogusConfig.objects.filter(
                id__in=[c.id for c in not_found_configs]
            ).update(found_in_api=False)

        return result

    def import_zaaktype_configs(self) -> ImportResult[ZaakTypeConfig]:
        """
        Import zaaktype configurations from the ZGW API.

        This collapses individual ZaakType versions on their identificatie and catalog.

        Returns:
            ImportResult with created/updated/excluded zaaktypen
        """
        result = ImportResult[ZaakTypeConfig]()

        try:
            zaak_types = self.catalogi_client.fetch_zaaktypes_no_cache()
        except Exception as exc:
            logger.exception(
                "Failed to fetch zaaktypen from ZGW API",
                client=self.catalogi_client,
            )
            result.excluded.append(
                ExcludedObject(
                    object_type="ZaakType",
                    url=self.catalogi_client.configured_from.api_root,
                    reason=ExclusionReason.API_ERROR,
                    error_message=str(exc),
                )
            )
            return result

        # Filter out internal zaaktypen and track excluded
        filtered_zaak_types = []
        for zt in zaak_types:
            if zt.indicatie_intern_of_extern == "extern":
                filtered_zaak_types.append(zt)
            else:
                result.excluded.append(
                    ExcludedObject(
                        object_type="ZaakType",
                        url=zt.url,
                        identificatie=zt.identificatie,
                        reason=ExclusionReason.FILTERED_INTERNAL,
                        extra_context={
                            "omschrijving": zt.omschrijving,
                            "catalogus": zt.catalogus,
                        },
                    )
                )

        catalog_lookup = {c.url: c for c in CatalogusConfig.objects.all()}
        existing_ztc = {
            (ztc.catalogus_id, ztc.identificatie): ztc
            for ztc in ZaakTypeConfig.objects.filter(
                catalogus__service=self.zgw_api_group.ztc_service
            )
        }

        zaaktype_keys_seen = set()
        for zaak_type in filtered_zaak_types:
            try:
                catalog = catalog_lookup[zaak_type.catalogus]
            except KeyError:
                result.excluded.append(
                    ExcludedObject(
                        object_type="ZaakType",
                        url=zaak_type.url,
                        identificatie=zaak_type.identificatie,
                        reason=ExclusionReason.MISSING_CATALOGUS,
                        error_message=f"Catalogus {zaak_type.catalogus} niet geconfigureerd for ZaakType",
                        extra_context={"omschrijving": zaak_type.omschrijving},
                    )
                )
                continue

            key = (catalog.id, zaak_type.identificatie)
            zaaktype_keys_seen.add(key)

            if ztc := existing_ztc.get(key):
                # Update existing
                updated = False

                # Update URL list if this zaaktype URL is not already tracked
                if zaak_type.url not in ztc.urls:
                    ztc.urls = ztc.urls + [zaak_type.url]
                    updated = True

                # Update omschrijving if changed
                if ztc.omschrijving != zaak_type.omschrijving:
                    ztc.omschrijving = zaak_type.omschrijving
                    updated = True

                # Mark as found in API
                if not ztc.found_in_api:
                    ztc.found_in_api = True
                    updated = True

                if updated:
                    try:
                        ztc.save()
                        if ztc not in result.updated:
                            result.updated.append(ztc)
                    except Exception as exc:
                        logger.exception(
                            "Failed to update zaaktype config",
                            url=zaak_type.url,
                            identificatie=zaak_type.identificatie,
                            exc_info=exc,
                        )
                        result.excluded.append(
                            ExcludedObject(
                                object_type="ZaakType",
                                url=zaak_type.url,
                                identificatie=zaak_type.identificatie,
                                reason=ExclusionReason.DATABASE_ERROR,
                                error_message=f"Save failed: {exc}",
                            )
                        )
            else:
                # Create new
                ztc = ZaakTypeConfig(
                    urls=[zaak_type.url],
                    catalogus=catalog,
                    identificatie=zaak_type.identificatie,
                    omschrijving=zaak_type.omschrijving,
                    found_in_api=True,
                )
                try:
                    ztc.save()
                    result.created.append(ztc)
                    existing_ztc[key] = ztc
                except Exception as exc:
                    logger.exception(
                        "Failed to create zaaktype config",
                        url=zaak_type.url,
                        identificatie=zaak_type.identificatie,
                        exc_info=exc,
                    )
                    result.excluded.append(
                        ExcludedObject(
                            object_type="ZaakType",
                            url=zaak_type.url,
                            identificatie=zaak_type.identificatie,
                            reason=ExclusionReason.DATABASE_ERROR,
                            error_message=f"Save failed: {exc}",
                        )
                    )

        # Handle ZaakTypeConfig objects that were not seen in the API response
        not_found_configs = []
        for key, config in existing_ztc.items():
            if key not in zaaktype_keys_seen:
                # This zaaktype no longer exists in the API
                logger.info(
                    "ZaakType config exists in database but not found in API",
                    identificatie=config.identificatie,
                    catalogus_url=config.catalogus.url if config.catalogus else None,
                )
                not_found_configs.append(config)
                result.not_found_in_api.append(config)

        if not_found_configs:
            ZaakTypeConfig.objects.filter(
                id__in=[c.id for c in not_found_configs]
            ).update(found_in_api=False)

        return result

    def get_api_zaaktypen_for_saved_ztc(self, ztc: ZaakTypeConfig):
        return (
            zt
            for zt in self.catalogi_client.fetch_zaaktypes_no_cache(
                identificatie=ztc.identificatie
            )
            # Filter out internal zaaktypen (we don't track exclusions here since
            # they're already tracked in import_zaaktype_configs)
            if zt.indicatie_intern_of_extern == "extern"
            and zt.catalogus == ztc.catalogus_url
        )

    def import_informatieobjecttype_configs_for_zaaktype(
        self, ztc: ZaakTypeConfig
    ) -> ZaakTypeRelatedImportResult[ZaakTypeInformatieObjectTypeConfig]:
        """
        Import informatieobjecttype configurations for a specific zaaktype.

        Args:
            ztc: The ZaakTypeConfig to import informatieobjecttypen for

        Returns:
            ZaakTypeRelatedImportResult with created/updated/excluded informatieobjecttypen
        """
        result = ZaakTypeRelatedImportResult[ZaakTypeInformatieObjectTypeConfig](
            zaaktype_config=ztc
        )

        try:
            zaak_types = self.get_api_zaaktypen_for_saved_ztc(ztc)
        except Exception as exc:
            logger.exception(
                "Failed to fetch zaaktypes for informatieobjecttype import",
                identificatie=ztc.identificatie,
            )
            result.excluded.append(
                ExcludedObject(
                    object_type="InformatieObjectType",
                    url=ztc.urls[0] if ztc.urls else "",
                    identificatie=ztc.identificatie,
                    reason=ExclusionReason.API_ERROR,
                    error_message=str(exc),
                    extra_context={"zaaktype_identificatie": ztc.identificatie},
                )
            )
            return result

        # Collect and implicitly de-duplicate informatieobjecttype urls
        info_queue = defaultdict(list)
        for zaak_type in zaak_types:
            for url in zaak_type.informatieobjecttypen:
                info_queue[url].append(zaak_type)

        # Map existing config records by url and by omschrijving (natural key).
        # The omschrijving lookup is used to copy OIP config fields onto newly
        # created entries when OpenZaak produces a duplicate information object type
        # (same omschrijving, new URL) after a zaaktype edit.
        all_existing_iots = list(ztc.zaaktypeinformatieobjecttypeconfig_set.all())
        existing_map = {
            ztiotc.informatieobjecttype_url: ztiotc for ztiotc in all_existing_iots
        }
        existing_iot_by_omschrijving = {
            ztiotc.omschrijving: ztiotc for ztiotc in all_existing_iots
        }

        iot_urls_seen = set()
        if info_queue:
            for iot_url, using_zaak_types in info_queue.items():
                try:
                    info_type = (
                        self.catalogi_client.fetch_single_information_object_type(
                            iot_url
                        )
                    )
                except Exception as exc:
                    logger.exception(
                        "Unable to retrieve informatieobjecttype",
                        informatieobjecttype_url=iot_url,
                        exc_info=exc,
                    )
                    result.excluded.append(
                        ExcludedObject(
                            object_type="InformatieObjectType",
                            url=iot_url,
                            reason=ExclusionReason.API_ERROR,
                            error_message=str(exc),
                            extra_context={"zaaktype_identificatie": ztc.identificatie},
                        )
                    )
                    continue

                if not info_type:
                    result.excluded.append(
                        ExcludedObject(
                            object_type="InformatieObjectType",
                            url=iot_url,
                            reason=ExclusionReason.API_ERROR,
                            error_message="API returned None",
                            extra_context={"zaaktype_identificatie": ztc.identificatie},
                        )
                    )
                    continue

                iot_urls_seen.add(info_type.url)

                if ztiotc := existing_map.get(info_type.url):
                    # Update existing
                    updated = False

                    # Update omschrijving if changed
                    if ztiotc.omschrijving != info_type.omschrijving:
                        ztiotc.omschrijving = info_type.omschrijving
                        updated = True

                    # Track which zaaktype UUIDs use this informatieobjecttype
                    for using in using_zaak_types:
                        if using.uuid not in ztiotc.zaaktype_uuids:
                            ztiotc.zaaktype_uuids.append(using.uuid)
                            updated = True

                    # Mark as found in API
                    if not ztiotc.found_in_api:
                        ztiotc.found_in_api = True
                        updated = True

                    if updated:
                        try:
                            ztiotc.save()
                            if ztiotc not in result.updated:
                                result.updated.append(ztiotc)
                        except Exception as exc:
                            logger.exception(
                                "Failed to update informatieobjecttype config",
                                informatieobjecttype_url=info_type.url,
                                exc_info=exc,
                            )
                            result.excluded.append(
                                ExcludedObject(
                                    object_type="InformatieObjectType",
                                    url=info_type.url,
                                    reason=ExclusionReason.DATABASE_ERROR,
                                    error_message=f"Save failed: {exc}",
                                    extra_context={
                                        "zaaktype_identificatie": ztc.identificatie
                                    },
                                )
                            )
                else:
                    # Create new: if an existing entry with the same omschrijving
                    # exists, copy its OIP config fields so the admin does not have
                    # to reconfigure after OpenZaak duplicates an information object type.
                    config_source = existing_iot_by_omschrijving.get(
                        info_type.omschrijving
                    )
                    ztiotc = ZaakTypeInformatieObjectTypeConfig(
                        zaaktype_config=ztc,
                        informatieobjecttype_url=info_type.url,
                        omschrijving=info_type.omschrijving,
                        zaaktype_uuids=[zt.uuid for zt in using_zaak_types],
                        found_in_api=True,
                    )
                    if config_source is not None:
                        logger.info(
                            "Copying OIP config from existing information object type with matching omschrijving",
                            new_informatieobjecttype_url=info_type.url,
                            source_informatieobjecttype_url=config_source.informatieobjecttype_url,
                            omschrijving=info_type.omschrijving,
                        )
                        ztiotc.document_upload_enabled = (
                            config_source.document_upload_enabled
                        )
                        ztiotc.document_notification_enabled = (
                            config_source.document_notification_enabled
                        )
                    try:
                        ztiotc.save()
                        result.created.append(ztiotc)
                        existing_map[info_type.url] = ztiotc
                    except Exception as exc:
                        logger.exception(
                            "Failed to create informatieobjecttype config",
                            informatieobjecttype_url=info_type.url,
                            exc_info=exc,
                        )
                        result.excluded.append(
                            ExcludedObject(
                                object_type="InformatieObjectType",
                                url=info_type.url,
                                reason=ExclusionReason.DATABASE_ERROR,
                                error_message=f"Save failed: {exc}",
                                extra_context={
                                    "zaaktype_identificatie": ztc.identificatie
                                },
                            )
                        )

        # Handle InformatieObjectType configs that were not seen in the API response
        not_found_configs = []
        for iot_url in existing_map:
            if iot_url not in iot_urls_seen:
                # This informatieobjecttype is no longer associated with this zaaktype
                logger.info(
                    "InformatieObjectType config exists for zaaktype but not found in API",
                    informatieobjecttype_url=iot_url,
                    zaaktype_identificatie=ztc.identificatie,
                )
                config = existing_map[iot_url]
                not_found_configs.append(config)
                result.not_found_in_api.append(config)

        if not_found_configs:
            ZaakTypeInformatieObjectTypeConfig.objects.filter(
                id__in=[c.id for c in not_found_configs]
            ).update(found_in_api=False)

        return result

    def import_statustype_configs_for_zaaktype(
        self, ztc: ZaakTypeConfig
    ) -> ZaakTypeRelatedImportResult[ZaakTypeStatusTypeConfig]:
        """
        Import statustype configurations for a specific zaaktype.

        Args:
            ztc: The ZaakTypeConfig to import statustypen for

        Returns:
            ZaakTypeRelatedImportResult with created/updated/excluded statustypen
        """
        result = ZaakTypeRelatedImportResult[ZaakTypeStatusTypeConfig](
            zaaktype_config=ztc
        )

        try:
            zaak_types = self.get_api_zaaktypen_for_saved_ztc(ztc)
        except Exception as exc:
            logger.exception(
                "Failed to fetch zaaktypes for statustype import",
                identificatie=ztc.identificatie,
            )
            result.excluded.append(
                ExcludedObject(
                    object_type="StatusType",
                    url=ztc.urls[0] if ztc.urls else "",
                    identificatie=ztc.identificatie,
                    reason=ExclusionReason.API_ERROR,
                    error_message=str(exc),
                    extra_context={"zaaktype_identificatie": ztc.identificatie},
                )
            )
            return result

        # Collect and implicitly de-duplicate statustype urls
        status_queue = defaultdict(list)
        for zaak_type in zaak_types:
            for url in zaak_type.statustypen:
                status_queue[url].append(zaak_type)

        # Map existing config records by url and by omschrijving (natural key).
        # The omschrijving lookup is used to copy OIP config fields onto newly
        # created entries when OpenZaak produces a duplicate status type (same
        # omschrijving, new URL) after a zaaktype edit.
        all_existing_statustypes = list(ztc.zaaktypestatustypeconfig_set.all())
        existing_map = {
            ztstc.statustype_url: ztstc for ztstc in all_existing_statustypes
        }
        existing_statustype_by_omschrijving = {
            ztstc.omschrijving: ztstc for ztstc in all_existing_statustypes
        }

        statustype_urls_seen = set()
        if status_queue:
            for statustype_url, using_zaak_types in status_queue.items():
                try:
                    status_type = self.catalogi_client.fetch_single_status_type(
                        statustype_url
                    )
                except Exception as exc:
                    logger.exception(
                        "Unable to obtain statustype",
                        statustype_url=statustype_url,
                        exc_info=exc,
                    )
                    result.excluded.append(
                        ExcludedObject(
                            object_type="StatusType",
                            url=statustype_url,
                            reason=ExclusionReason.API_ERROR,
                            error_message=str(exc),
                            extra_context={"zaaktype_identificatie": ztc.identificatie},
                        )
                    )
                    continue

                if not status_type:
                    result.excluded.append(
                        ExcludedObject(
                            object_type="StatusType",
                            url=statustype_url,
                            reason=ExclusionReason.API_ERROR,
                            error_message="API returned None",
                            extra_context={"zaaktype_identificatie": ztc.identificatie},
                        )
                    )
                    continue

                statustype_urls_seen.add(status_type.url)

                if ztstc := existing_map.get(status_type.url):
                    # Update existing
                    updated = False

                    # Update all overlapping fields
                    if ztstc.omschrijving != status_type.omschrijving:
                        ztstc.omschrijving = status_type.omschrijving
                        updated = True

                    if ztstc.statustekst != status_type.statustekst:
                        ztstc.statustekst = status_type.statustekst
                        updated = True

                    # Track which zaaktype UUIDs use this statustype
                    for using in using_zaak_types:
                        if using.uuid not in ztstc.zaaktype_uuids:
                            ztstc.zaaktype_uuids.append(using.uuid)
                            updated = True

                    # Mark as found in API
                    if not ztstc.found_in_api:
                        ztstc.found_in_api = True
                        updated = True

                    if updated:
                        try:
                            ztstc.save()
                            if ztstc not in result.updated:
                                result.updated.append(ztstc)
                        except Exception as exc:
                            logger.exception(
                                "Failed to update statustype config",
                                statustype_url=status_type.url,
                                exc_info=exc,
                            )
                            result.excluded.append(
                                ExcludedObject(
                                    object_type="StatusType",
                                    url=status_type.url,
                                    reason=ExclusionReason.DATABASE_ERROR,
                                    error_message=f"Save failed: {exc}",
                                    extra_context={
                                        "zaaktype_identificatie": ztc.identificatie
                                    },
                                )
                            )
                else:
                    # Create new: if an existing entry with the same omschrijving
                    # exists, copy its OIP config fields so the admin does not have
                    # to reconfigure after OpenZaak duplicates a status type.
                    ztstc = ZaakTypeStatusTypeConfig(
                        zaaktype_config=ztc,
                        statustype_url=status_type.url,
                        omschrijving=status_type.omschrijving,
                        statustekst=status_type.statustekst,
                        zaaktype_uuids=[zt.uuid for zt in using_zaak_types],
                        found_in_api=True,
                    )
                    config_source = existing_statustype_by_omschrijving.get(
                        status_type.omschrijving
                    )
                    if config_source is not None:
                        logger.info(
                            "Copying OIP config from existing statustype with matching omschrijving",
                            new_statustype_url=status_type.url,
                            source_statustype_url=config_source.statustype_url,
                            omschrijving=status_type.omschrijving,
                        )
                        ztstc.status_indicator = config_source.status_indicator
                        ztstc.status_indicator_text = (
                            config_source.status_indicator_text
                        )
                        ztstc.document_upload_description = (
                            config_source.document_upload_description
                        )
                        ztstc.description = config_source.description
                        ztstc.notify_status_change = config_source.notify_status_change
                        ztstc.action_required = config_source.action_required
                        ztstc.document_upload_enabled = (
                            config_source.document_upload_enabled
                        )
                        ztstc.call_to_action_url = config_source.call_to_action_url
                        ztstc.call_to_action_text = config_source.call_to_action_text
                        ztstc.case_link_text = config_source.case_link_text
                    try:
                        ztstc.save()
                        result.created.append(ztstc)
                        existing_map[status_type.url] = ztstc
                    except Exception as exc:
                        logger.exception(
                            "Failed to create statustype config",
                            statustype_url=status_type.url,
                            exc_info=exc,
                        )
                        result.excluded.append(
                            ExcludedObject(
                                object_type="StatusType",
                                url=status_type.url,
                                reason=ExclusionReason.DATABASE_ERROR,
                                error_message=f"Save failed: {exc}",
                                extra_context={
                                    "zaaktype_identificatie": ztc.identificatie
                                },
                            )
                        )

        # Handle StatusType configs that were not seen in the API response
        not_found_configs = []
        for statustype_url in existing_map:
            if statustype_url not in statustype_urls_seen:
                # This statustype is no longer associated with this zaaktype
                logger.info(
                    "StatusType config exists for zaaktype but not found in API",
                    statustype_url=statustype_url,
                    zaaktype_identificatie=ztc.identificatie,
                )
                config = existing_map[statustype_url]
                not_found_configs.append(config)
                result.not_found_in_api.append(config)

        if not_found_configs:
            ZaakTypeStatusTypeConfig.objects.filter(
                id__in=[c.id for c in not_found_configs]
            ).update(found_in_api=False)

        return result

    def import_resultaattype_configs_for_zaaktype(
        self, ztc: ZaakTypeConfig
    ) -> ZaakTypeRelatedImportResult[ZaakTypeResultaatTypeConfig]:
        """
        Import resultaattype configurations for a specific zaaktype.

        Args:
            ztc: The ZaakTypeConfig to import resultaattypen for

        Returns:
            ZaakTypeRelatedImportResult with created/updated/excluded resultaattypen
        """
        result = ZaakTypeRelatedImportResult[ZaakTypeResultaatTypeConfig](
            zaaktype_config=ztc
        )

        try:
            zaak_types = self.get_api_zaaktypen_for_saved_ztc(ztc)
        except Exception as exc:
            logger.exception(
                "Failed to fetch zaaktypes for resultaattype import",
                identificatie=ztc.identificatie,
            )
            result.excluded.append(
                ExcludedObject(
                    object_type="ResultaatType",
                    url=ztc.urls[0] if ztc.urls else "",
                    identificatie=ztc.identificatie,
                    reason=ExclusionReason.API_ERROR,
                    error_message=str(exc),
                    extra_context={"zaaktype_identificatie": ztc.identificatie},
                )
            )
            return result

        # Map existing config records by url and by omschrijving (natural key).
        # The omschrijving lookup is used to copy OIP config fields onto newly
        # created entries when OpenZaak produces a duplicate result type (same
        # omschrijving, new URL) after a zaaktype edit.
        all_existing_resultaattypes = list(ztc.zaaktyperesultaattypeconfig_set.all())
        existing_map = {
            ztrtc.resultaattype_url: ztrtc for ztrtc in all_existing_resultaattypes
        }
        existing_resultaattype_by_omschrijving = {
            ztrtc.omschrijving: ztrtc for ztrtc in all_existing_resultaattypes
        }

        # Collect and implicitly de-duplicate resultaattype urls
        resultaat_queue = defaultdict(list)
        for zaak_type in zaak_types:
            for url in zaak_type.resultaattypen:
                resultaat_queue[url].append(zaak_type)

        resultaattype_urls_seen = set()
        if resultaat_queue:
            for resultaattype_url, using_zaak_types in resultaat_queue.items():
                try:
                    resultaat_type = self.catalogi_client.fetch_single_resultaat_type(
                        resultaattype_url
                    )
                except Exception as exc:
                    logger.exception(
                        "Unable to obtain resultaattype",
                        resultaattype_url=resultaattype_url,
                        exc_info=exc,
                    )
                    result.excluded.append(
                        ExcludedObject(
                            object_type="ResultaatType",
                            url=resultaattype_url,
                            reason=ExclusionReason.API_ERROR,
                            error_message=str(exc),
                            extra_context={"zaaktype_identificatie": ztc.identificatie},
                        )
                    )
                    continue

                if not resultaat_type:
                    result.excluded.append(
                        ExcludedObject(
                            object_type="ResultaatType",
                            url=resultaattype_url,
                            reason=ExclusionReason.API_ERROR,
                            error_message="API returned None",
                            extra_context={"zaaktype_identificatie": ztc.identificatie},
                        )
                    )
                    continue

                resultaattype_urls_seen.add(resultaat_type.url)

                if ztrtc := existing_map.get(resultaat_type.url):
                    # Update existing
                    updated = False

                    # Update omschrijving if changed
                    if ztrtc.omschrijving != resultaat_type.omschrijving:
                        ztrtc.omschrijving = resultaat_type.omschrijving
                        updated = True

                    # Track which zaaktype UUIDs use this resultaattype
                    for using in using_zaak_types:
                        if using.uuid not in ztrtc.zaaktype_uuids:
                            ztrtc.zaaktype_uuids.append(using.uuid)
                            updated = True

                    # Mark as found in API
                    if not ztrtc.found_in_api:
                        ztrtc.found_in_api = True
                        updated = True

                    if updated:
                        try:
                            ztrtc.save()
                            if ztrtc not in result.updated:
                                result.updated.append(ztrtc)
                        except Exception as exc:
                            logger.exception(
                                "Failed to update resultaattype config",
                                resultaattype_url=resultaat_type.url,
                                exc_info=exc,
                            )
                            result.excluded.append(
                                ExcludedObject(
                                    object_type="ResultaatType",
                                    url=resultaat_type.url,
                                    reason=ExclusionReason.DATABASE_ERROR,
                                    error_message=f"Save failed: {exc}",
                                    extra_context={
                                        "zaaktype_identificatie": ztc.identificatie
                                    },
                                )
                            )
                else:
                    # Create new: if an existing entry with the same omschrijving
                    # exists, copy its OIP config fields so the admin does not have
                    # to reconfigure after OpenZaak duplicates a result type.
                    config_source = existing_resultaattype_by_omschrijving.get(
                        resultaat_type.omschrijving
                    )
                    ztrtc = ZaakTypeResultaatTypeConfig(
                        zaaktype_config=ztc,
                        resultaattype_url=resultaat_type.url,
                        omschrijving=resultaat_type.omschrijving,
                        zaaktype_uuids=[zt.uuid for zt in using_zaak_types],
                        found_in_api=True,
                    )
                    if config_source is not None:
                        logger.info(
                            "Copying OIP config from existing resultaattype with matching omschrijving",
                            new_resultaattype_url=resultaat_type.url,
                            source_resultaattype_url=config_source.resultaattype_url,
                            omschrijving=resultaat_type.omschrijving,
                        )
                        ztrtc.description = config_source.description
                    try:
                        ztrtc.save()
                        result.created.append(ztrtc)
                        existing_map[resultaat_type.url] = ztrtc
                    except Exception as exc:
                        logger.exception(
                            "Failed to create resultaattype config",
                            resultaattype_url=resultaat_type.url,
                            exc_info=exc,
                        )
                        result.excluded.append(
                            ExcludedObject(
                                object_type="ResultaatType",
                                url=resultaat_type.url,
                                reason=ExclusionReason.DATABASE_ERROR,
                                error_message=f"Save failed: {exc}",
                                extra_context={
                                    "zaaktype_identificatie": ztc.identificatie
                                },
                            )
                        )

        # Handle ResultaatType configs that were not seen in the API response
        not_found_configs = []
        for resultaattype_url in existing_map:
            if resultaattype_url not in resultaattype_urls_seen:
                # This resultaattype is no longer associated with this zaaktype
                logger.info(
                    "ResultaatType config exists for zaaktype but not found in API",
                    resultaattype_url=resultaattype_url,
                    zaaktype_identificatie=ztc.identificatie,
                )
                config = existing_map[resultaattype_url]
                not_found_configs.append(config)
                result.not_found_in_api.append(config)

        if not_found_configs:
            ZaakTypeResultaatTypeConfig.objects.filter(
                id__in=[c.id for c in not_found_configs]
            ).update(found_in_api=False)

        return result
