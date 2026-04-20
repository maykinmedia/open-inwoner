import dataclasses
from datetime import date

from open_inwoner.haalcentraal.api_models import BRP2xPersoon, BRP13Persoon


@dataclasses.dataclass
class BRPData:
    """Flat presentation model used by the mydata template (profile view)."""

    # match with user model fields
    first_name: str = ""
    infix: str = ""
    last_name: str = ""

    street: str = ""
    housenumber: str = ""
    houseletter: str = ""
    housenumbersuffix: str = ""

    city: str = ""
    birthday: date | None = None

    # extra fields for My Data
    initials: str = ""
    birth_place: str = ""
    gender: str = ""
    postal_code: str = ""
    country: str = ""

    def get_housenumber(self):
        parts = []
        if self.housenumber:
            parts.append(str(self.housenumber))
        if self.houseletter:
            parts.append(str(self.houseletter))
        if self.housenumbersuffix:
            parts.append(" ")
            parts.append(str(self.housenumbersuffix))
        return "".join(parts)

    @classmethod
    def from_persoon(cls, persoon: BRP13Persoon | BRP2xPersoon) -> "BRPData":
        match persoon:
            case BRP13Persoon():
                vp = persoon.verblijfplaats
                street = vp.straat
                housenumber = str(vp.huisnummer or "")
                houseletter = vp.huisletter
                housenumbersuffix = vp.huisnummertoevoeging
                city = vp.woonplaats
                postal_code = vp.postcode
                country = vp.land.omschrijving
                gender = persoon.geslachtsaanduiding
            case BRP2xPersoon():
                va = persoon.verblijfplaats.verblijfadres
                street = va.officieleStraatnaam
                housenumber = str(va.huisnummer or "")
                houseletter = va.huisletter
                housenumbersuffix = va.huisnummertoevoeging
                city = va.woonplaats
                postal_code = va.postcode
                country = ""
                gender = persoon.geslacht.omschrijving
            case _:
                raise ValueError(f"Unexpected BRP persoon type: {type(persoon)}")

        return cls(
            first_name=persoon.naam.voornamen,
            infix=persoon.naam.voorvoegsel,
            last_name=persoon.naam.geslachtsnaam,
            initials=persoon.naam.voorletters,
            birthday=persoon.geboorte.datum.datum,
            birth_place=persoon.geboorte.plaats.omschrijving,
            gender=gender,
            street=street,
            housenumber=housenumber,
            houseletter=houseletter,
            housenumbersuffix=housenumbersuffix,
            city=city,
            postal_code=postal_code,
            country=country,
        )
