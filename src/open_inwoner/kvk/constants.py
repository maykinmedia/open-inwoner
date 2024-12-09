from typing import Literal, Optional, TypedDict

from django.db import models
from django.utils.translation import gettext_lazy as _


class CompanyType(models.TextChoices):
    hoofdvestiging = "hoofdvestiging", _("Hoofdvestiging")
    nevenvestiging = "nevenvestiging", _("Nevenvestiging")
    rechtspersoon = "rechtspersoon", _("Rechtspersoon")


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
    adres: BedrijfsAdres
    type: BedrijfsType
    actief: Optional[str]
    vervallenNaam: Optional[str]
    _links: Optional[dict]
