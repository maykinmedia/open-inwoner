from dataclasses import dataclass, field

from open_inwoner.ssd.service.jaaropgave.fwi_include_resolved import (
    Adres,
    Persoon,
    StandaardBedrag,
    StdIndJn,
)
from open_inwoner.ssd.service.jaaropgave.fwi_resolved import Fwi, NietsGevonden

__NAMESPACE__ = "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400"


@dataclass
class Inhoudingsplichtige:
    gemeentecode: str | None = field(
        default=None,
        metadata={
            "name": "Gemeentecode",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 4,
            "pattern": r"\d*",
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
    bezoekadres: str | None = field(
        default=None,
        metadata={
            "name": "Bezoekadres",
            "type": "Element",
            "namespace": "",
            "max_length": 30,
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


@dataclass
class Loonheffingskorting:
    ingangsdatum: str | None = field(
        default=None,
        metadata={
            "name": "Ingangsdatum",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 8,
            "pattern": r"[1-2][0-9]{3}(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])",
        },
    )
    cd_loonheffingskorting: object | None = field(
        default=None,
        metadata={
            "name": "CdLoonheffingskorting",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Client(Persoon):
    adres: Adres | None = field(
        default=None,
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class SpecificatieJaarOpgave:
    regeling: str | None = field(
        default=None,
        metadata={
            "name": "Regeling",
            "type": "Element",
            "namespace": "",
            "required": True,
            "max_length": 30,
        },
    )
    dienstjaar: int | None = field(
        default=None,
        metadata={
            "name": "Dienstjaar",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": 1980,
            "max_inclusive": 2999,
        },
    )
    aangifte_periode_van: str | None = field(
        default=None,
        metadata={
            "name": "AangiftePeriodeVan",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 8,
            "pattern": r"[1-2][0-9]{3}(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])",
        },
    )
    aangifte_periode_tot: str | None = field(
        default=None,
        metadata={
            "name": "AangiftePeriodeTot",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 8,
            "pattern": r"[1-2][0-9]{3}(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])",
        },
    )
    fiscaalloon: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "Fiscaalloon",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    loonheffing: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "Loonheffing",
            "type": "Element",
            "namespace": "",
        },
    )
    cd_premie_volksverzekering: object | None = field(
        default=None,
        metadata={
            "name": "CdPremieVolksverzekering",
            "type": "Element",
            "namespace": "",
        },
    )
    indicatie_zvw: StdIndJn | None = field(
        default=None,
        metadata={
            "name": "IndicatieZVW",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    ingehouden_premie_zvw: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "IngehoudenPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    vergoeding_premie_zvw: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "VergoedingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_fiscaalloon: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "OntvangstenFiscaalloon",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_ingehouden_premie_zvw: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "OntvangstenIngehoudenPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_vergoeding_premie_zvw: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "OntvangstenVergoedingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_premieloon: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "OntvangstenPremieloon",
            "type": "Element",
            "namespace": "",
        },
    )
    werkgeversheffing_premie_zvw: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "WerkgeversheffingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_werkgeversheffing_premie_zvw: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "OntvangstenWerkgeversheffingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    loonheffingskorting: list[Loonheffingskorting] = field(
        default_factory=list,
        metadata={
            "name": "Loonheffingskorting",
            "type": "Element",
            "namespace": "",
            "max_occurs": 3,
        },
    )
    belaste_alimentatie: StandaardBedrag | None = field(
        default=None,
        metadata={
            "name": "BelasteAlimentatie",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class JaarOpgave:
    inhoudingsplichtige: Inhoudingsplichtige | None = field(
        default=None,
        metadata={
            "name": "Inhoudingsplichtige",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    specificatie_jaar_opgave: list[SpecificatieJaarOpgave] = field(
        default_factory=list,
        metadata={
            "name": "SpecificatieJaarOpgave",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )


@dataclass
class JaarOpgaveClient:
    client: Client | None = field(
        default=None,
        metadata={
            "name": "Client",
            "type": "Element",
            "namespace": "",
        },
    )
    jaar_opgave: list[JaarOpgave] = field(
        default_factory=list,
        metadata={
            "name": "JaarOpgave",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Response:
    jaar_opgave_client: JaarOpgaveClient | None = field(
        default=None,
        metadata={
            "name": "JaarOpgaveClient",
            "type": "Element",
            "namespace": "",
        },
    )
    fwi: Fwi | None = field(
        default=None,
        metadata={
            "name": "FWI",
            "type": "Element",
            "namespace": "http://www.centric.nl/GWS/FWI/v0200",
        },
    )
    niets_gevonden: NietsGevonden | None = field(
        default=None,
        metadata={
            "name": "NietsGevonden",
            "type": "Element",
            "namespace": "http://www.centric.nl/GWS/FWI/v0200",
        },
    )


@dataclass
class JaarOpgaveInfoResponse(Response):
    class Meta:
        namespace = "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400"
