from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

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
    bedrijfsnaam: Optional[str] = field(
        default=None,
        metadata={
            "name": "Bedrijfsnaam",
            "type": "Element",
            "namespace": "",
            "max_length": 100,
        },
    )
    gemeentecode: Optional[str] = field(
        default=None,
        metadata={
            "name": "Gemeentecode",
            "type": "Element",
            "namespace": "",
            "length": 4,
            "pattern": r"\d*",
        },
    )
    applicatie_naam: Optional[str] = field(
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
    locatie: Optional[str] = field(
        default=None,
        metadata={
            "name": "Locatie",
            "type": "Element",
            "namespace": "",
            "max_length": 35,
        },
    )
    straatnaam: Optional[str] = field(
        default=None,
        metadata={
            "name": "Straatnaam",
            "type": "Element",
            "namespace": "",
            "max_length": 24,
        },
    )
    huisnummer: Optional[int] = field(
        default=None,
        metadata={
            "name": "Huisnummer",
            "type": "Element",
            "namespace": "",
            "total_digits": 5,
        },
    )
    huisletter: Optional[str] = field(
        default=None,
        metadata={
            "name": "Huisletter",
            "type": "Element",
            "namespace": "",
            "pattern": r"([A-Z]{1}|[a-z]{1})",
        },
    )
    huisnr_toevoeging: Optional[str] = field(
        default=None,
        metadata={
            "name": "HuisnrToevoeging",
            "type": "Element",
            "namespace": "",
            "max_length": 6,
        },
    )
    postcode: Optional[str] = field(
        default=None,
        metadata={
            "name": "Postcode",
            "type": "Element",
            "namespace": "",
            "length": 6,
            "pattern": r"[1-9][0-9]{3}[A-Z]{2}",
        },
    )
    woonplaatsnaam: Optional[str] = field(
        default=None,
        metadata={
            "name": "Woonplaatsnaam",
            "type": "Element",
            "namespace": "",
            "max_length": 80,
        },
    )
    gemeentenaam: Optional[str] = field(
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


class StdIndJn(Enum):
    """
    :cvar VALUE_0: Nee
    :cvar VALUE_1: Ja
    """

    VALUE_0 = "0"
    VALUE_1 = "1"


@dataclass
class Persoon:
    burger_service_nr: Optional[str] = field(
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
    voornamen: Optional[str] = field(
        default=None,
        metadata={
            "name": "Voornamen",
            "type": "Element",
            "namespace": "",
            "max_length": 200,
            "pattern": r"\D*",
        },
    )
    voorletters: Optional[str] = field(
        default=None,
        metadata={
            "name": "Voorletters",
            "type": "Element",
            "namespace": "",
            "max_length": 12,
            "pattern": r"\D*",
        },
    )
    voorvoegsel: Optional[str] = field(
        default=None,
        metadata={
            "name": "Voorvoegsel",
            "type": "Element",
            "namespace": "",
            "max_length": 10,
            "pattern": r"\D*",
        },
    )
    achternaam: Optional[str] = field(
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
    aanduiding_naamgebruik: Optional[AanduidingNaamgebruik] = field(
        default=None,
        metadata={
            "name": "AanduidingNaamgebruik",
            "type": "Element",
            "namespace": "",
        },
    )
    voorvoegsel_echtgenoot: Optional[str] = field(
        default=None,
        metadata={
            "name": "VoorvoegselEchtgenoot",
            "type": "Element",
            "namespace": "",
            "max_length": 10,
            "pattern": r"\D*",
        },
    )
    achternaam_echtgenoot: Optional[str] = field(
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
    cd_positief_negatief: Optional[CdPositiefNegatief] = field(
        default=None,
        metadata={
            "name": "CdPositiefNegatief",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    waarde_bedrag: Optional[int] = field(
        default=None,
        metadata={
            "name": "WaardeBedrag",
            "type": "Element",
            "namespace": "",
            "required": True,
            "total_digits": 18,
        },
    )
