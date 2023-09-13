from dataclasses import dataclass, field
from typing import List, Optional

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
    gemeentecode: Optional[str] = field(
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
    gemeentenaam: Optional[str] = field(
        default=None,
        metadata={
            "name": "Gemeentenaam",
            "type": "Element",
            "namespace": "",
            "max_length": 40,
        },
    )
    bezoekadres: Optional[str] = field(
        default=None,
        metadata={
            "name": "Bezoekadres",
            "type": "Element",
            "namespace": "",
            "max_length": 30,
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


@dataclass
class Loonheffingskorting:
    ingangsdatum: Optional[str] = field(
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
    cd_loonheffingskorting: Optional[object] = field(
        default=None,
        metadata={
            "name": "CdLoonheffingskorting",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Client(Persoon):
    adres: Optional[Adres] = field(
        default=None,
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class SpecificatieJaarOpgave:
    regeling: Optional[str] = field(
        default=None,
        metadata={
            "name": "Regeling",
            "type": "Element",
            "namespace": "",
            "required": True,
            "max_length": 30,
        },
    )
    dienstjaar: Optional[int] = field(
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
    aangifte_periode_van: Optional[str] = field(
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
    aangifte_periode_tot: Optional[str] = field(
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
    fiscaalloon: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "Fiscaalloon",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    loonheffing: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "Loonheffing",
            "type": "Element",
            "namespace": "",
        },
    )
    cd_premie_volksverzekering: Optional[object] = field(
        default=None,
        metadata={
            "name": "CdPremieVolksverzekering",
            "type": "Element",
            "namespace": "",
        },
    )
    indicatie_zvw: Optional[StdIndJn] = field(
        default=None,
        metadata={
            "name": "IndicatieZVW",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    ingehouden_premie_zvw: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "IngehoudenPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    vergoeding_premie_zvw: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "VergoedingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_fiscaalloon: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "OntvangstenFiscaalloon",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_ingehouden_premie_zvw: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "OntvangstenIngehoudenPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_vergoeding_premie_zvw: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "OntvangstenVergoedingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_premieloon: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "OntvangstenPremieloon",
            "type": "Element",
            "namespace": "",
        },
    )
    werkgeversheffing_premie_zvw: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "WerkgeversheffingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    ontvangsten_werkgeversheffing_premie_zvw: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "OntvangstenWerkgeversheffingPremieZVW",
            "type": "Element",
            "namespace": "",
        },
    )
    loonheffingskorting: List[Loonheffingskorting] = field(
        default_factory=list,
        metadata={
            "name": "Loonheffingskorting",
            "type": "Element",
            "namespace": "",
            "max_occurs": 3,
        },
    )
    belaste_alimentatie: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "BelasteAlimentatie",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class JaarOpgave:
    inhoudingsplichtige: Optional[Inhoudingsplichtige] = field(
        default=None,
        metadata={
            "name": "Inhoudingsplichtige",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    specificatie_jaar_opgave: List[SpecificatieJaarOpgave] = field(
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
    client: Optional[Client] = field(
        default=None,
        metadata={
            "name": "Client",
            "type": "Element",
            "namespace": "",
        },
    )
    jaar_opgave: List[JaarOpgave] = field(
        default_factory=list,
        metadata={
            "name": "JaarOpgave",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Response:
    jaar_opgave_client: Optional[JaarOpgaveClient] = field(
        default=None,
        metadata={
            "name": "JaarOpgaveClient",
            "type": "Element",
            "namespace": "",
        },
    )
    fwi: Optional[Fwi] = field(
        default=None,
        metadata={
            "name": "FWI",
            "type": "Element",
            "namespace": "http://www.centric.nl/GWS/FWI/v0200",
        },
    )
    niets_gevonden: Optional[NietsGevonden] = field(
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
