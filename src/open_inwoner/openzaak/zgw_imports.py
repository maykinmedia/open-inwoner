from collections import defaultdict
from typing import List, Tuple

from django.db import transaction

from zgw_consumers.api_models.catalogi import (
    InformatieObjectType,
    ResultaatType,
    StatusType,
)

from open_inwoner.openzaak.api_models import ZaakType
from open_inwoner.openzaak.catalog import (
    fetch_case_types_by_identification_no_cache,
    fetch_catalogs_no_cache,
    fetch_single_information_object_type,
    fetch_single_resultaat_type,
    fetch_single_status_type,
    fetch_zaaktypes_no_cache,
)
from open_inwoner.openzaak.models import (
    CatalogusConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)


def filter_zaaktypes(case_types: List[ZaakType]) -> List[ZaakType]:
    return [c for c in case_types if c.indicatie_intern_of_extern == "extern"]


def get_configurable_zaaktypes() -> List[ZaakType]:
    case_types = fetch_zaaktypes_no_cache()
    case_types = filter_zaaktypes(case_types)
    return case_types


def get_configurable_zaaktypes_by_identification(
    identificatie, catalogus_url
) -> List[ZaakType]:
    case_types = fetch_case_types_by_identification_no_cache(
        identificatie, catalogus_url
    )
    case_types = filter_zaaktypes(case_types)
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
                    rsin=catalog.rsin or "",
                    domein=catalog.domein,
                )
            )

        if create:
            CatalogusConfig.objects.bulk_create(create)

    return create


def import_zaaktype_configs() -> List[ZaakTypeConfig]:
    """
    generate a ZaakTypeConfig for every ZaakType.identificatie in the ZGW API

    this collapses individual ZaakType versions on their identificatie and catalog
    """
    zaak_types = get_configurable_zaaktypes()
    if not zaak_types:
        return []

    create = {}

    with transaction.atomic():
        catalog_lookup = {c.url: c for c in CatalogusConfig.objects.all()}

        known_keys = set(
            ZaakTypeConfig.objects.values_list("catalogus_id", "identificatie")
        )

        for zaak_type in zaak_types:
            catalog = None
            if zaak_type.catalogus:
                catalog = catalog_lookup.get(zaak_type.catalogus)
                if not catalog:
                    # weird edge-case: if the zaak_type has a catalogus-url but we don't have the object
                    # TODO this is bad, log/raise something
                    pass

            # make key for de-duplication and collapsing related zaak-types on their 'identificatie'
            if catalog:
                key = (catalog.id, zaak_type.identificatie)
            else:
                key = (None, zaak_type.identificatie)

            if key not in known_keys:
                known_keys.add(key)
                create[key] = ZaakTypeConfig(
                    urls=[zaak_type.url],
                    catalogus=catalog,
                    identificatie=zaak_type.identificatie,
                    omschrijving=zaak_type.omschrijving,
                )
            elif key in create:
                create[key].urls = create[key].urls + [zaak_type.url]

        if create:
            ZaakTypeConfig.objects.bulk_create(list(create.values()))

    return list((create or {}).values())


def import_zaaktype_informatieobjecttype_configs() -> List[
    Tuple[ZaakTypeConfig, InformatieObjectType]
]:
    """
    generate ZaakTypeInformatieObjectTypeConfigs for all ZaakTypeConfig
    """
    created = []
    for ztc in ZaakTypeConfig.objects.all():
        imported = import_zaaktype_informatieobjecttype_configs_for_type(ztc)
        if imported:
            created.append((ztc, imported))
    return created


def import_zaaktype_statustype_configs() -> List[Tuple[ZaakTypeConfig, StatusType]]:
    """
    generate ZaakTypeStatusTypeConfigs for all ZaakTypeConfig
    """
    created = []
    for ztc in ZaakTypeConfig.objects.all():
        imported = import_statustype_configs_for_type(ztc)
        if imported:
            created.append((ztc, imported))
    return created


def import_zaaktype_resultaattype_configs() -> List[
    Tuple[ZaakTypeConfig, ResultaatType]
]:
    """
    generate ZaakTypeResultaatTypeConfigs for all ZaakTypeConfig
    """
    created = []
    for ztc in ZaakTypeConfig.objects.all():
        imported = import_resultaattype_configs_for_type(ztc)
        if imported:
            created.append((ztc, imported))
    return created


def import_zaaktype_informatieobjecttype_configs_for_type(
    ztc: ZaakTypeConfig,
) -> List[ZaakTypeInformatieObjectTypeConfig]:
    """
    generate ZaakTypeInformatieObjectTypeConfigs for all InformationObjectTypes used by each ZaakTypeConfigs source ZaakTypes

    this is a bit complicated because one ZaakTypeConfig can represent multiple ZaakTypes
    """

    # grab actual ZaakTypes for this identificatie
    zaak_types: List[ZaakType] = get_configurable_zaaktypes_by_identification(
        ztc.identificatie, ztc.catalogus_url
    )
    if not zaak_types:
        return []

    create = []
    update = []

    with transaction.atomic():
        # map existing config records by url
        info_map = {
            ztiotc.informatieobjecttype_url: ztiotc
            for ztiotc in ztc.zaaktypeinformatieobjecttypeconfig_set.all()
        }

        # collect and implicitly de-duplicate informatieobjecttype url's and track which zaaktype used it
        info_queue = defaultdict(list)
        for zaak_type in zaak_types:
            for url in zaak_type.informatieobjecttypen:
                info_queue[url].append(zaak_type)

        if info_queue:
            # load urls and update/create records
            for iot_url, using_zaak_types in info_queue.items():
                info_type = fetch_single_information_object_type(iot_url)

                ztiotc = info_map.get(info_type.url)
                if ztiotc:
                    # we got a record for this, see if we got data to update
                    for using in using_zaak_types:
                        # track which zaaktype UUID's are interested in this informationobjecttype
                        if using.uuid not in ztiotc.zaaktype_uuids:
                            ztiotc.zaaktype_uuids.append(using.uuid)
                            if ztiotc not in create:
                                update.append(ztiotc)
                else:
                    # new record
                    ztiotc = ZaakTypeInformatieObjectTypeConfig(
                        zaaktype_config=ztc,
                        informatieobjecttype_url=info_type.url,
                        omschrijving=info_type.omschrijving,
                        zaaktype_uuids=[zt.uuid for zt in using_zaak_types],
                    )
                    create.append(ztiotc)
                    # not strictly necessary but let's be accurate
                    info_map[info_type.uuid] = ztiotc

        if create:
            ZaakTypeInformatieObjectTypeConfig.objects.bulk_create(create)
        if update:
            ZaakTypeInformatieObjectTypeConfig.objects.bulk_update(
                update, ["zaaktype_uuids"]
            )

    return create


def import_statustype_configs_for_type(
    ztc: ZaakTypeConfig,
) -> List[ZaakTypeStatusTypeConfig]:
    """
    generate ZaakTypeStatusTypeConfigs for all StatusTypes used by each ZaakTypeConfigs source ZaakTypes

    this is a bit complicated because one ZaakTypeConfig can represent multiple ZaakTypes
    """

    # grab actual ZaakTypes for this identificatie
    zaak_types: List[ZaakType] = get_configurable_zaaktypes_by_identification(
        ztc.identificatie, ztc.catalogus_url
    )
    if not zaak_types:
        return []

    create = []
    update = []

    with transaction.atomic():
        # map existing config records by url

        info_map = {
            zaaktype_statustype.statustype_url: zaaktype_statustype
            for zaaktype_statustype in ztc.zaaktypestatustypeconfig_set.all()
        }

        # collect and implicitly de-duplicate statustype url's and track which zaaktype used it
        info_queue = defaultdict(list)
        for zaak_type in zaak_types:
            for url in zaak_type.statustypen:
                info_queue[url].append(zaak_type)

        if info_queue:
            # load urls and update/create records
            for statustype_url, using_zaak_types in info_queue.items():
                status_type = fetch_single_status_type(statustype_url)
                if not status_type:  # Statustype isn't available anymore?
                    continue

                zaaktype_statustype = info_map.get(status_type.url)
                if zaaktype_statustype:
                    # we got a record for this, see if we got data to update
                    for using in using_zaak_types:
                        # track which zaaktype UUID's are interested in this statustype
                        if using.uuid not in zaaktype_statustype.zaaktype_uuids:
                            zaaktype_statustype.zaaktype_uuids.append(using.uuid)
                            if zaaktype_statustype not in create:
                                update.append(zaaktype_statustype)
                else:
                    # new record
                    zaaktype_statustype = ZaakTypeStatusTypeConfig(
                        zaaktype_config=ztc,
                        statustype_url=status_type.url,
                        omschrijving=status_type.omschrijving,
                        statustekst=status_type.statustekst,
                        zaaktype_uuids=[zt.uuid for zt in using_zaak_types],
                    )
                    create.append(zaaktype_statustype)
                    # not strictly necessary but let's be accurate
                    info_map[status_type.uuid] = zaaktype_statustype

        if create:
            ZaakTypeStatusTypeConfig.objects.bulk_create(create)
        if update:
            ZaakTypeStatusTypeConfig.objects.bulk_update(update, ["zaaktype_uuids"])

    return create


def import_resultaattype_configs_for_type(
    ztc: ZaakTypeConfig,
) -> List[ZaakTypeResultaatTypeConfig]:
    """
    generate ZaakTypeResultaatTypeConfigs for all ResultaatTypes used by each ZaakTypeConfigs source ZaakTypes

    this is a bit complicated because one ZaakTypeConfig can represent multiple ZaakTypes
    """

    # grab actual ZaakTypes for this identificatie
    zaak_types: List[ZaakType] = get_configurable_zaaktypes_by_identification(
        ztc.identificatie, ztc.catalogus_url
    )
    if not zaak_types:
        return []

    create = []
    update = []

    with transaction.atomic():
        # map existing config records by url

        info_map = {
            zaaktype_resultaattype.resultaattype_url: zaaktype_resultaattype
            for zaaktype_resultaattype in ztc.zaaktyperesultaattypeconfig_set.all()
        }

        # collect and implicitly de-duplicate resultaattype url's and track which zaaktype used it
        info_queue = defaultdict(list)
        for zaak_type in zaak_types:
            for url in zaak_type.resultaattypen:
                info_queue[url].append(zaak_type)

        if info_queue:
            # load urls and update/create records
            for resultaattype_url, using_zaak_types in info_queue.items():
                resultaat_type = fetch_single_resultaat_type(resultaattype_url)

                zaaktype_resultaattype = info_map.get(resultaat_type.url)
                if zaaktype_resultaattype:
                    # we got a record for this, see if we got data to update
                    for using in using_zaak_types:
                        # track which zaaktype UUID's are interested in this resultaattype
                        if using.uuid not in zaaktype_resultaattype.zaaktype_uuids:
                            zaaktype_resultaattype.zaaktype_uuids.append(using.uuid)
                            if zaaktype_resultaattype not in create:
                                update.append(zaaktype_resultaattype)
                else:
                    # new record
                    zaaktype_resultaattype = ZaakTypeResultaatTypeConfig(
                        zaaktype_config=ztc,
                        resultaattype_url=resultaat_type.url,
                        omschrijving=resultaat_type.omschrijving,
                        zaaktype_uuids=[zt.uuid for zt in using_zaak_types],
                    )
                    create.append(zaaktype_resultaattype)
                    # not strictly necessary but let's be accurate
                    info_map[resultaat_type.uuid] = zaaktype_resultaattype

        if create:
            ZaakTypeResultaatTypeConfig.objects.bulk_create(create)
        if update:
            ZaakTypeResultaatTypeConfig.objects.bulk_update(update, ["zaaktype_uuids"])

    return create
