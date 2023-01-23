from collections import namedtuple
from typing import List, Tuple

from django.db import transaction
from django.utils.formats import date_format

from open_inwoner.openzaak.api_models import ZaakType
from open_inwoner.openzaak.catalog import fetch_catalog_zaaktypes, fetch_catalogs
from open_inwoner.openzaak.models import CatalogusConfig, ZaakTypeConfig


def get_configurable_zaaktypes(catalog: CatalogusConfig) -> List[ZaakType]:
    case_types = fetch_catalog_zaaktypes(catalog.url)
    # TODO filter zaaktypes we're not interested in
    #  like intern/extern, concept etc
    return case_types


SortChoice = namedtuple("SortChoice", ["sort", "choice"])


def get_configurable_zaaktype_choices(
    catalog: CatalogusConfig,
) -> List[Tuple[str, str]]:
    case_types = get_configurable_zaaktypes(catalog)
    if not case_types:
        return []

    known = set(catalog.zaaktypeconfig_set.values_list("identificatie", flat=True))

    options = []
    for case_type in case_types:
        label = f"{case_type.identificatie} - {case_type.omschrijving}"
        if case_type.concept:
            label = f"{label} (concept)"
        if case_type.identificatie in known:
            label = f"{label} (*)"

        if case_type.begin_geldigheid:
            label = f"{label} (begin {date_format(case_type.begin_geldigheid)})"
        if case_type.einde_geldigheid:
            label = f"{label} (einde {date_format(case_type.einde_geldigheid)})"

        options.append(
            # use tuple to sort without i8n date format confusion
            SortChoice(
                sort=(label, case_type.begin_geldigheid, case_type.einde_geldigheid),
                choice=(str(case_type.identificatie), label),
            )
        )

    options.sort(key=lambda sc: sc.sort)
    return [sc.choice for sc in options]


def import_catalog_configs() -> List[CatalogusConfig]:
    catalogs = fetch_catalogs()
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
