from typing import NotRequired

from typing_extensions import TypedDict


class ListThemaParams(TypedDict, total=False):
    """Query parameters for listing themas."""

    naam: str
    parent: str
    page: int


class NestedProductType(TypedDict):
    """Nested ProductType object in Thema responses."""

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


class Thema(TypedDict):
    """Thema (theme) response object."""

    uuid: str
    naam: str
    beschrijving: NotRequired[str]
    gepubliceerd: NotRequired[bool]
    aanmaak_datum: str
    update_datum: str
    hoofd_thema: str | None
    producttypen: NotRequired[list[NestedProductType]]
