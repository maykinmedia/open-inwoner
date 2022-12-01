from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from zgw_consumers.api_models.base import ZGWModel
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

"""
Modified ZGWModel's to work with both OpenZaak and e-Suite implementations,
because there is an issue where e-Suite doesn't return all JSON fields the official API and dataclasses expect
"""


@dataclass
class Zaak(ZGWModel):
    url: str
    identificatie: str
    bronorganisatie: str
    omschrijving: str
    #    toelichting: str
    zaaktype: str
    registratiedatum: date
    startdatum: date
    einddatum_gepland: Optional[date]
    uiterlijke_einddatum_afdoening: Optional[date]
    #    publicatiedatum: Optional[date]
    vertrouwelijkheidaanduiding: str
    status: str
    einddatum: Optional[date] = None
    resultaat: Optional[str] = None
    #    relevante_andere_zaken: list
    #    zaakgeometrie: dict


@dataclass
class ZaakType(ZGWModel):
    url: str
    # catalogus: str
    identificatie: str
    omschrijving: str
    vertrouwelijkheidaanduiding: str
    doel: str
    aanleiding: str
    indicatie_intern_of_extern: str
    handeling_initiator: str
    onderwerp: str
    handeling_behandelaar: str
    # doorlooptijd: relativedelta
    # servicenorm: Optional[relativedelta]
    # opschorting_en_aanhouding_mogelijk: bool
    # verlenging_mogelijk: bool
    # verlengingstermijn: Optional[relativedelta]
    # publicatie_indicatie: bool
    # producten_of_diensten: list
    statustypen: list
    # resultaattypen: list
    # informatieobjecttypen: list
    # roltypen: list
    # besluittypen: list

    # begin_geldigheid: date
    # versiedatum: date


@dataclass
class ZaakInformatieObject(ZGWModel):
    url: str
    informatieobject: str
    zaak: str
    # aard_relatie_weergave: str
    titel: str
    # beschrijving: str
    registratiedatum: datetime


@dataclass
class InformatieObject(ZGWModel):
    url: str
    identificatie: str
    bronorganisatie: str
    creatiedatum: date
    titel: str
    vertrouwelijkheidaanduiding: str
    auteur: str
    status: str
    formaat: str
    taal: str
    versie: int
    # beginRegistratie: datetime
    bestandsnaam: str
    inhoud: str
    bestandsomvang: int
    link: str
    beschrijving: str
    ontvangstdatum: str
    verzenddatum: str
    # indicatieGebruiksrecht: str
    ondertekening: dict  # {'soort': '', 'datum': None}
    integriteit: dict  # {'algoritme': '', 'waarde': '', 'datum': None}
    informatieobjecttype: str
    locked: bool
    # bestandsdelen: List[str]


@dataclass
class Rol(ZGWModel):
    url: str
    zaak: str
    betrokkene_type: str
    roltype: str
    omschrijving: str
    omschrijving_generiek: str
    roltoelichting: str
    indicatie_machtiging: Optional[str] = ""
    registratiedatum: Optional[datetime] = None
    betrokkene: Optional[str] = ""
    betrokkene_identificatie: Optional[dict] = None

    def get_betrokkene_type_display(self):
        return RolTypes.values[self.betrokkene_type]

    def get_omschrijving_generiek_display(self):
        return RolOmschrijving.values[self.omschrijving_generiek]


@dataclass
class Resultaat(ZGWModel):
    url: str
    zaak: str
    resultaattype: str
    toelichting: Optional[str] = ""


@dataclass
class Status(ZGWModel):
    url: str
    zaak: str
    statustype: str
    datum_status_gezet: Optional[datetime] = None
    statustoelichting: Optional[str] = ""
