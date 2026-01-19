from typing import NotRequired

from typing_extensions import TypedDict


class ListProductTypeParams(TypedDict, total=False):
    """Query parameters for listing product types."""

    naam: str
    thema: str
    page: int
    themas__naam: str
    themas__naam__in: list[str]
    themas__uuid: str
    themas__uuid__in: list[str]
    locaties__naam__contains: str
    locaties__uuid: str
    locaties__uuid__in: list[str]


class NestedThema(TypedDict):
    """Nested Thema object in ProductType responses."""

    uuid: str
    naam: str
    beschrijving: NotRequired[str]
    gepubliceerd: NotRequired[bool]
    aanmaak_datum: str
    update_datum: str
    hoofd_thema: str


class Locatie(TypedDict):
    """Locatie (location) object."""

    uuid: str
    naam: str
    straatnaam: NotRequired[str]
    huisnummer: NotRequired[str]
    postcode: NotRequired[str]
    plaats: NotRequired[str]


class Organisatie(TypedDict):
    """Organisatie (organization) object."""

    uuid: str
    naam: str
    code: NotRequired[str]


class Contact(TypedDict):
    """Contact object."""

    uuid: str
    naam: str
    email: NotRequired[str]
    telefoonnummer: NotRequired[str]


class PrijsOptie(TypedDict):
    """Price option object."""

    uuid: str
    bedrag: str
    beschrijving: str


class PrijsRegel(TypedDict):
    """Price rule object."""

    uuid: str
    url: str
    beschrijving: str
    mapping: NotRequired[dict | None]


class NestedPrijs(TypedDict):
    """Nested Prijs object in ProductType responses."""

    uuid: str
    prijsopties: NotRequired[list[PrijsOptie]]
    prijsregels: NotRequired[list[PrijsRegel]]
    actief_vanaf: str


class NestedLink(TypedDict):
    """Nested Link object."""

    uuid: str
    naam: str
    url: str


class NestedActie(TypedDict):
    """Nested Actie object."""

    uuid: str
    naam: str
    type: NotRequired[str]


class NestedBestand(TypedDict):
    """Nested Bestand (file) object."""

    uuid: str
    naam: str
    url: str


class NestedExterneCode(TypedDict):
    """Nested Externe Code object."""

    uuid: str
    code: str
    bron: NotRequired[str]


class NestedParameter(TypedDict):
    """Nested Parameter object."""

    uuid: str
    naam: str
    waarde: NotRequired[str]


class ProductType(TypedDict):
    """ProductType response object."""

    uuid: str
    url: NotRequired[str]
    naam: str
    samenvatting: NotRequired[str]
    uniforme_product_naam: NotRequired[str | None]
    doelgroep: NotRequired[str]
    code: str
    keywords: NotRequired[list[str]]
    toegestane_statussen: NotRequired[list[str]]
    gepubliceerd: bool
    publicatie_start_datum: NotRequired[str | None]
    publicatie_eind_datum: NotRequired[str | None]
    aanmaak_datum: str
    update_datum: str
    themas: list[NestedThema]
    locaties: NotRequired[list[Locatie]]
    organisaties: NotRequired[list[Organisatie]]
    contacten: NotRequired[list[Contact]]
    prijzen: NotRequired[list[NestedPrijs]]
    links: NotRequired[list[NestedLink]]
    acties: NotRequired[list[NestedActie]]
    bestanden: NotRequired[list[NestedBestand]]
    externe_codes: NotRequired[list[NestedExterneCode]]
    parameters: NotRequired[list[NestedParameter]]
    taal: NotRequired[str]
    verbruiksobject_schema: NotRequired[dict | None]
    dataobject_schema: NotRequired[dict | None]
    interne_opmerkingen: NotRequired[str]
