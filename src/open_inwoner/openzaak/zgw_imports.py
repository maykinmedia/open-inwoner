import logging
from typing import cast

from django.db import transaction

from zgw_consumers.api_models.catalogi import (
    StatusType,
)

from open_inwoner.openzaak.api_models import ZaakType
from open_inwoner.openzaak.clients import (
    CatalogiClient,
    build_zgw_client_from_service,
)
from open_inwoner.openzaak.models import (
    ZaakTypeConfig,
    ZaakTypeStatusTypeConfig,
)

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


def filter_zaaktypes(case_types: list[ZaakType]) -> list[ZaakType]:
    return [c for c in case_types if c.indicatie_intern_of_extern == "extern"]


def get_configurable_zaaktypes(case_types: list[ZaakType]) -> list[ZaakType]:
    case_types = filter_zaaktypes(case_types)
    return case_types


def get_configurable_zaaktypes_by_identification(
    client: CatalogiClient, identificatie, catalogus_url
) -> list[ZaakType]:
    case_types = client.fetch_case_types_by_identification_no_cache(
        identificatie, catalogus_url
    )
    case_types = filter_zaaktypes(case_types)
    return case_types


def import_statustype_configs_for_type(
    ztc: ZaakTypeConfig,
) -> list[ZaakTypeStatusTypeConfig]:
    """
    generate ZaakTypeStatusTypeConfigs for all StatusTypes used by each ZaakTypeConfigs source ZaakTypes

    this is a bit complicated because one ZaakTypeConfig can represent multiple ZaakTypes
    """
    client = cast(CatalogiClient, build_zgw_client_from_service(ztc.catalogus.service))
    if not client:
        logger.warning(
            "Not importing statustype configs: could not build Catalogi API client"
        )
        return []

    # grab actual ZaakTypes for this identificatie
    zaak_types: list[ZaakType] = get_configurable_zaaktypes_by_identification(
        client, ztc.identificatie, ztc.catalogus_url
    )
    if not zaak_types:
        logger.info("No zaaktypes found in the API")
        return []

    created = []

    with transaction.atomic():
        for zaak_type in zaak_types:
            # load urls and update/create records
            for statustype_url in zaak_type.statustypen:
                logger.info("Fetching status_type for url %s", statustype_url)
                status_type = cast(
                    StatusType | None, client.fetch_single_status_type(statustype_url)
                )
                if not status_type:  # Statustype isn't available anymore?
                    logger.warning("No statustype found for url: %s", statustype_url)
                    continue

                # new record
                zaaktype_statustype = ZaakTypeStatusTypeConfig.objects.create(
                    zaaktype_config=ztc,
                    statustype_url=status_type.url,
                    omschrijving=status_type.omschrijving,
                    statustekst=status_type.statustekst,
                    zaaktype_uuids=[zaak_type.uuid],
                )
                logger.info("created %s", zaaktype_statustype)
                created.append(zaaktype_statustype)

    return created


def run_fix():
    zt = ZaakTypeConfig.objects.get(identificatie="ZAAKTYPE-2025-0000000001")
    result = import_statustype_configs_for_type(zt)
    print(result)
