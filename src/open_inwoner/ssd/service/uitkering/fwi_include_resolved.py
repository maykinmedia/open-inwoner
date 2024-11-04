from dataclasses import dataclass, field
from enum import Enum

__NAMESPACE__ = "http://www.centric.nl/GWS/Basisschema/v0400"


class AanduidingNaamgebruik(Enum):
    """
    :cvar VALUE_0: Onbekend
    :cvar VALUE_1: Eigen naam
    :cvar VALUE_2: Naam echtgeno(o)te of geregistreerd partner
    :cvar VALUE_3: Naam echtgeno(o)te of geregistreerd partner gevolgd
        door eigen naam
    :cvar VALUE_4: Eigen naam gevolgd door naam echtgeno(o)te of
        geregistreerd partner
    :cvar VALUE_5: Pseudoniem
    """

    VALUE_0 = "0"
    VALUE_1 = "1"
    VALUE_2 = "2"
    VALUE_3 = "3"
    VALUE_4 = "4"
    VALUE_5 = "5"


@dataclass
class Actor:
    bedrijfsnaam: str | None = field(
        default=None,
        metadata={
            "name": "Bedrijfsnaam",
            "type": "Element",
            "namespace": "",
            "max_length": 100,
        },
    )
    gemeentecode: str | None = field(
        default=None,
        metadata={
            "name": "Gemeentecode",
            "type": "Element",
            "namespace": "",
            "length": 4,
            "pattern": r"\d*",
        },
    )
    applicatie_naam: str | None = field(
        default=None,
        metadata={
            "name": "ApplicatieNaam",
            "type": "Element",
            "namespace": "",
            "max_length": 100,
        },
    )


@dataclass
class Adres:
    locatie: str | None = field(
        default=None,
        metadata={
            "name": "Locatie",
            "type": "Element",
            "namespace": "",
            "max_length": 35,
        },
    )
    straatnaam: str | None = field(
        default=None,
        metadata={
            "name": "Straatnaam",
            "type": "Element",
            "namespace": "",
            "max_length": 24,
        },
    )
    huisnummer: int | None = field(
        default=None,
        metadata={
            "name": "Huisnummer",
            "type": "Element",
            "namespace": "",
            "total_digits": 5,
        },
    )
    huisletter: str | None = field(
        default=None,
        metadata={
            "name": "Huisletter",
            "type": "Element",
            "namespace": "",
            "pattern": r"([A-Z]{1}|[a-z]{1})",
        },
    )
    huisnr_toevoeging: str | None = field(
        default=None,
        metadata={
            "name": "HuisnrToevoeging",
            "type": "Element",
            "namespace": "",
            "max_length": 6,
        },
    )
    postcode: str | None = field(
        default=None,
        metadata={
            "name": "Postcode",
            "type": "Element",
            "namespace": "",
            "length": 6,
            "pattern": r"[1-9][0-9]{3}[A-Z]{2}",
        },
    )
    woonplaatsnaam: str | None = field(
        default=None,
        metadata={
            "name": "Woonplaatsnaam",
            "type": "Element",
            "namespace": "",
            "max_length": 80,
        },
    )
    gemeentenaam: str | None = field(
        default=None,
        metadata={
            "name": "Gemeentenaam",
            "type": "Element",
            "namespace": "",
            "max_length": 40,
        },
    )


class CdPositiefNegatief(Enum):
    """
    :cvar VALUE: Positief
    :cvar VALUE_1: Negatief
    """

    VALUE = "+"
    VALUE_1 = "-"


class IndicatieKolom(Enum):
    """
    :cvar VALUE_0: Niet afdrukken
    :cvar VALUE_1: Pluskolom
    :cvar VALUE_2: Minkolom
    :cvar VALUE_3: Basiskolom
    """

    VALUE_0 = "0"
    VALUE_1 = "1"
    VALUE_2 = "2"
    VALUE_3 = "3"


class TypePeriode(Enum):
    """
    :cvar VALUE_0: Periode betrekking
    :cvar VALUE_1: Periode verwerking
    """

    VALUE_0 = "0"
    VALUE_1 = "1"


@dataclass
class Persoon:
    burger_service_nr: str | None = field(
        default=None,
        metadata={
            "name": "BurgerServiceNr",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 9,
            "pattern": r"\d*",
        },
    )
    voornamen: str | None = field(
        default=None,
        metadata={
            "name": "Voornamen",
            "type": "Element",
            "namespace": "",
            "max_length": 200,
            "pattern": r"\D*",
        },
    )
    voorletters: str | None = field(
        default=None,
        metadata={
            "name": "Voorletters",
            "type": "Element",
            "namespace": "",
            "max_length": 12,
            "pattern": r"\D*",
        },
    )
    voorvoegsel: str | None = field(
        default=None,
        metadata={
            "name": "Voorvoegsel",
            "type": "Element",
            "namespace": "",
            "max_length": 10,
            "pattern": r"\D*",
        },
    )
    achternaam: str | None = field(
        default=None,
        metadata={
            "name": "Achternaam",
            "type": "Element",
            "namespace": "",
            "required": True,
            "max_length": 200,
            "pattern": r"\D*",
        },
    )
    aanduiding_naamgebruik: AanduidingNaamgebruik | None = field(
        default=None,
        metadata={
            "name": "AanduidingNaamgebruik",
            "type": "Element",
            "namespace": "",
        },
    )
    voorvoegsel_echtgenoot: str | None = field(
        default=None,
        metadata={
            "name": "VoorvoegselEchtgenoot",
            "type": "Element",
            "namespace": "",
            "max_length": 10,
            "pattern": r"\D*",
        },
    )
    achternaam_echtgenoot: str | None = field(
        default=None,
        metadata={
            "name": "AchternaamEchtgenoot",
            "type": "Element",
            "namespace": "",
            "max_length": 200,
            "pattern": r"\D*",
        },
    )


@dataclass
class StandaardBedrag:
    cd_positief_negatief: CdPositiefNegatief | None = field(
        default=None,
        metadata={
            "name": "CdPositiefNegatief",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    waarde_bedrag: int | None = field(
        default=None,
        metadata={
            "name": "WaardeBedrag",
            "type": "Element",
            "namespace": "",
            "required": True,
            "total_digits": 18,
        },
    )
