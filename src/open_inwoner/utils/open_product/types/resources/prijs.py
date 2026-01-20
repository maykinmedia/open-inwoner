from typing import NotRequired

from typing_extensions import TypedDict


class ListPrijsParams(TypedDict, total=False):
    """Query parameters for listing prijzen (prices)."""

    product_type: str
    product_type__uuid: str
    product_type__uuid__in: list[str]
    actieve_datum: str
    actieve_datum__gte: str
    actieve_datum__lte: str
    page: int


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


class Prijs(TypedDict):
    """Prijs (price) response object."""

    uuid: str
    producttype_uuid: str
    prijsopties: NotRequired[list[PrijsOptie]]
    prijsregels: NotRequired[list[PrijsRegel]]
    actief_vanaf: str
