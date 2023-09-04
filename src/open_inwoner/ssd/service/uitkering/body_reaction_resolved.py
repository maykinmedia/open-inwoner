from dataclasses import dataclass, field
from typing import List, Optional

from open_inwoner.ssd.service.uitkering.fwi_include_resolved import (
    Adres,
    IndicatieKolom,
    Persoon,
    StandaardBedrag,
    TypePeriode,
)
from open_inwoner.ssd.service.uitkering.fwi_resolved import Fwi, NietsGevonden

__NAMESPACE__ = "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600"


@dataclass
class Uitkeringsinstantie:
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
class Client(Persoon):
    clientnummer: Optional[str] = field(
        default=None,
        metadata={
            "name": "Clientnummer",
            "type": "Element",
            "namespace": "",
            "max_length": 10,
            "pattern": r"\d*",
        },
    )


@dataclass
class Componenthistorie:
    omschrijving: Optional[str] = field(
        default=None,
        metadata={
            "name": "Omschrijving",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    bedrag: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "Bedrag",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    indicatie_kolom: Optional[IndicatieKolom] = field(
        default=None,
        metadata={
            "name": "IndicatieKolom",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    toelichting: Optional[str] = field(
        default=None,
        metadata={
            "name": "Toelichting",
            "type": "Element",
            "namespace": "",
            "max_length": 40,
        },
    )
    crediteur: Optional[str] = field(
        default=None,
        metadata={
            "name": "Crediteur",
            "type": "Element",
            "namespace": "",
            "max_length": 200,
        },
    )


@dataclass
class ClientType(Client):
    adres: Optional[Adres] = field(
        default=None,
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class OverigeBijstandspartij(Client):
    uitbetaald_bedrag: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "UitbetaaldBedrag",
            "type": "Element",
            "namespace": "",
        },
    )
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "Iban",
            "type": "Element",
            "namespace": "",
            "pattern": r"[A-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "Bic",
            "type": "Element",
            "namespace": "",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )


@dataclass
class Dossierhistorie:
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
    dossiernummer: Optional[str] = field(
        default=None,
        metadata={
            "name": "Dossiernummer",
            "type": "Element",
            "namespace": "",
            "required": True,
            "max_length": 8,
            "pattern": r"\d*",
        },
    )
    periodenummer: Optional[str] = field(
        default=None,
        metadata={
            "name": "Periodenummer",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 6,
            "pattern": r"[1-2][0-9]{3}(0[1-9]|1[0-2])",
        },
    )
    betrekkingsperiode: Optional[str] = field(
        default=None,
        metadata={
            "name": "Betrekkingsperiode",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 6,
            "pattern": r"[1-2][0-9]{3}(0[1-9]|1[0-2])",
        },
    )
    uitbetaald_bedrag_client: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "UitbetaaldBedragClient",
            "type": "Element",
            "namespace": "",
        },
    )
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "Iban",
            "type": "Element",
            "namespace": "",
            "pattern": r"[A-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "Bic",
            "type": "Element",
            "namespace": "",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    overige_bijstandspartij: List[OverigeBijstandspartij] = field(
        default_factory=list,
        metadata={
            "name": "OverigeBijstandspartij",
            "type": "Element",
            "namespace": "",
        },
    )
    opgegeven_inkomsten: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "OpgegevenInkomsten",
            "type": "Element",
            "namespace": "",
        },
    )
    te_verrekenen_inkomsten: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "TeVerrekenenInkomsten",
            "type": "Element",
            "namespace": "",
        },
    )
    inkomsten_vrijlating: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "InkomstenVrijlating",
            "type": "Element",
            "namespace": "",
        },
    )
    inkomsten_na_vrijlating: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "InkomstenNaVrijlating",
            "type": "Element",
            "namespace": "",
        },
    )
    vakantiegeld_over_inkomsten: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "VakantiegeldOverInkomsten",
            "type": "Element",
            "namespace": "",
        },
    )
    gekorte_inkomsten: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "GekorteInkomsten",
            "type": "Element",
            "namespace": "",
        },
    )
    uitbetaald_bedrag_dossier: Optional[StandaardBedrag] = field(
        default=None,
        metadata={
            "name": "UitbetaaldBedragDossier",
            "type": "Element",
            "namespace": "",
        },
    )
    datum_betaald: Optional[str] = field(
        default=None,
        metadata={
            "name": "DatumBetaald",
            "type": "Element",
            "namespace": "",
            "length": 8,
            "pattern": r"[1-2][0-9]{3}(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])",
        },
    )
    componenthistorie: List[Componenthistorie] = field(
        default_factory=list,
        metadata={
            "name": "Componenthistorie",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Uitkeringsspecificatie:
    uitkeringsinstantie: Optional[Uitkeringsinstantie] = field(
        default=None,
        metadata={
            "name": "Uitkeringsinstantie",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    dossierhistorie: List[Dossierhistorie] = field(
        default_factory=list,
        metadata={
            "name": "Dossierhistorie",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )


@dataclass
class UitkeringsSpecificatieClient:
    client: Optional[ClientType] = field(
        default=None,
        metadata={
            "name": "Client",
            "type": "Element",
            "namespace": "",
        },
    )
    type_periode: Optional[TypePeriode] = field(
        default=None,
        metadata={
            "name": "TypePeriode",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    uitkeringsspecificatie: List[Uitkeringsspecificatie] = field(
        default_factory=list,
        metadata={
            "name": "Uitkeringsspecificatie",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Response:
    uitkerings_specificatie_client: Optional[UitkeringsSpecificatieClient] = field(
        default=None,
        metadata={
            "name": "UitkeringsSpecificatieClient",
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
class UitkeringsSpecificatieInfoResponse(Response):
    class Meta:
        namespace = (
            "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600"
        )
