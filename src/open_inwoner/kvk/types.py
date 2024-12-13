from typing import Literal, Optional

from pydantic import TypeAdapter
from typing_extensions import TypedDict

AdresType = Literal["bezoekadres", "postadres"]
BedrijfsType = Literal["hoofdvestiging", "nevenvestiging", "rechtspersoon"]


class BedrijfsBinnenlandsAdres(TypedDict, total=False):
    type: AdresType
    plaats: Optional[str]
    postcode: Optional[str]
    straatnaam: Optional[str]
    huisnummer: Optional[str]
    huisletter: Optional[str]
    postbusnummer: Optional[str]


class BedrijfsBuitenlandsAdres(TypedDict, total=False):
    straatHuisnummer: Optional[str]
    postcodeWoonplaats: Optional[str]
    land: str


class BedrijfsAdres(TypedDict, total=False):
    binnenlandsAdres: Optional[BedrijfsBinnenlandsAdres]
    buitenlandsAdres: Optional[BedrijfsBuitenlandsAdres]


class Bedrijf(TypedDict, total=False):
    kvkNummer: str
    rsin: Optional[str]
    vestigingsnummer: Optional[str]
    naam: str
    adres: Optional[BedrijfsAdres]
    type: BedrijfsType
    actief: Optional[str]
    vervallenNaam: Optional[str]
    _links: Optional[dict]


BedrijfValidator = TypeAdapter(Bedrijf)
