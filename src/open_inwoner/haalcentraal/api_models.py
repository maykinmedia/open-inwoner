from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class Waardetabel(BaseModel):
    """Codelist entry; only omschrijving is read."""

    omschrijving: str = ""


class BRPDatum(BaseModel):
    datum: date | None = None

    @field_validator("datum", mode="before")
    @classmethod
    def coerce_datum(cls, v):
        """Return None for any date string that isn't strict YYYY-MM-DD."""
        if v is None or isinstance(v, date):
            return v
        try:
            return datetime.strptime(str(v), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None


class BRPNaam(BaseModel):
    voornamen: str = ""
    voorvoegsel: str = ""
    geslachtsnaam: str = ""
    voorletters: str = ""


class BRPGeboorte(BaseModel):
    datum: BRPDatum = Field(default_factory=BRPDatum)
    plaats: Waardetabel = Field(default_factory=Waardetabel)


class BRPAdres(BaseModel):
    """Common house-number fields shared by both API versions."""

    huisnummer: int | None = None
    huisletter: str = ""
    huisnummertoevoeging: str = ""
    woonplaats: str = ""
    postcode: str = ""


# BRP 1.3 (flat verblijfplaats)
class BRP13Verblijfplaats(BRPAdres):
    straat: str = ""
    land: Waardetabel = Field(default_factory=Waardetabel)


class BRP13Persoon(BaseModel):
    naam: BRPNaam = Field(default_factory=BRPNaam)
    geslachtsaanduiding: str = ""
    geboorte: BRPGeboorte = Field(default_factory=BRPGeboorte)
    verblijfplaats: BRP13Verblijfplaats = Field(default_factory=BRP13Verblijfplaats)


# BRP 2.x (nested verblijfadres)
class BRPVerblijfadres(BRPAdres):
    officieleStraatnaam: str = ""


class BRPVerblijfplaats2x(BaseModel):
    verblijfadres: BRPVerblijfadres = Field(default_factory=BRPVerblijfadres)


class BRP2xPersoon(BaseModel):
    naam: BRPNaam = Field(default_factory=BRPNaam)
    geslacht: Waardetabel = Field(default_factory=Waardetabel)
    geboorte: BRPGeboorte = Field(default_factory=BRPGeboorte)
    verblijfplaats: BRPVerblijfplaats2x = Field(default_factory=BRPVerblijfplaats2x)
