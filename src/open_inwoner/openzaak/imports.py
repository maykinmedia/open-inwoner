from typing import List

from django.db import transaction

from open_inwoner.openzaak.api_models import ZaakType
from open_inwoner.openzaak.catalog import (
    fetch_catalogs_no_cache,
    fetch_zaaktypes_no_cache,
)
from open_inwoner.openzaak.models import CatalogusConfig, ZaakTypeConfig


def get_configurable_zaaktypes() -> List[ZaakType]:
    case_types = fetch_zaaktypes_no_cache()
    # TODO filter zaaktypes we're never interested in?
    #  like intern/extern, concept etc

    return case_types


def import_catalog_configs() -> List[CatalogusConfig]:
    """
    generate a CatalogusConfig for every catalog in the ZGW API

    note this doesn't generate anything on eSuite
    """
    catalogs = fetch_catalogs_no_cache()
    if not catalogs:
        return []

    create = []

    with transaction.atomic():
        known = set(CatalogusConfig.objects.values_list("url", flat=True))
        for catalog in catalogs:
            if catalog.url in known:
                continue
            create.append(
                CatalogusConfig(
                    url=catalog.url,
                    rsin=catalog.rsin,
                    domein=catalog.domein,
                )
            )

        if create:
            CatalogusConfig.objects.bulk_create(create)

    return create


def import_zaaktype_configs() -> List[ZaakType]:
    """
    generate a ZaakTypeConfig for every ZaakType.identificatie in the ZGW API

    this collapses individual ZaakType version on their identificatie and catalog
    """
    zaak_types = get_configurable_zaaktypes()
    if not zaak_types:
        return []

    create = []

    with transaction.atomic():
        catalog_lookup = {c.url: c for c in CatalogusConfig.objects.all()}

        known_keys = set(
            ZaakTypeConfig.objects.values_list("catalogus_id", "identificatie")
        )

        for zaak_type in zaak_types:
            # deal with
            catalog = catalog_lookup.get(zaak_type.catalogus)
            if catalog:
                key = (catalog.id, zaak_type.identificatie)
            else:
                key = (None, zaak_type.identificatie)

            if key not in known_keys:
                known_keys.add(key)
                create.append(
                    ZaakTypeConfig(
                        catalogus=catalog,
                        identificatie=zaak_type.identificatie,
                        omschrijving=zaak_type.omschrijving,
                    )
                )

        if create:
            ZaakTypeConfig.objects.bulk_create(create)

    return create
