from typing import NotRequired

from typing_extensions import TypedDict


class ListProductParams(TypedDict, total=False):
    """Query parameters for listing products."""

    naam: str
    product_type: str
    page: int
    eigenaren__bsn: str


class Eigenaar(TypedDict):
    """Eigenaar (owner) object."""

    uuid: str
    bsn: NotRequired[str]
    kvk_nummer: NotRequired[str]
    vestigingsnummer: NotRequired[str]
    klantnummer: NotRequired[str]


class NestedThema(TypedDict):
    """Nested Thema object in Product responses."""

    uuid: str
    naam: str
    beschrijving: NotRequired[str]
    gepubliceerd: NotRequired[bool]
    aanmaak_datum: str
    update_datum: str
    hoofd_thema: str
    publicatie_start_datum: NotRequired[str]
    publicatie_eind_datum: NotRequired[str]


class NestedProductType(TypedDict):
    """Nested ProductType object in Product responses."""

    uuid: str
    code: str
    keywords: NotRequired[list[str]]
    uniforme_product_naam: str
    toegestane_statussen: NotRequired[list[str]]
    gepubliceerd: bool
    publicatie_start_datum: NotRequired[str | None]
    publicatie_eind_datum: NotRequired[str | None]
    aanmaak_datum: str
    update_datum: str
    themas: list[NestedThema]


class NestedDocument(TypedDict):
    """Nested Document reference."""

    urn: NotRequired[str | None]
    url: NotRequired[str | None]


class NestedZaak(TypedDict):
    """Nested Zaak reference."""

    urn: NotRequired[str | None]
    url: NotRequired[str | None]


class NestedTaak(TypedDict):
    """Nested Taak reference."""

    urn: NotRequired[str | None]
    url: NotRequired[str | None]


class Product(TypedDict):
    """Product response object."""

    uuid: str
    url: str
    naam: NotRequired[str]
    start_datum: NotRequired[str | None]
    eind_datum: NotRequired[str | None]
    aanmaak_datum: str
    update_datum: str
    producttype: NestedProductType
    gepubliceerd: NotRequired[bool]
    eigenaren: list[Eigenaar]
    documenten: NotRequired[list[NestedDocument]]
    zaken: NotRequired[list[NestedZaak]]
    taken: NotRequired[list[NestedTaak]]
    status: NotRequired[str]
    prijs: NotRequired[str | None]
    frequentie: NotRequired[str]
    verbruiksobject: NotRequired[dict | None]
    dataobject: NotRequired[dict | None]
    aanvraag_zaak_urn: NotRequired[str | None]
    aanvraag_zaak_url: NotRequired[str | None]
