from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from dateutil.relativedelta import relativedelta
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
    zaaktype: str
    registratiedatum: date
    startdatum: date
    status: str
    vertrouwelijkheidaanduiding: str
    toelichting: Optional[str] = None
    einddatum_gepland: Optional[date] = None
    uiterlijke_einddatum_afdoening: Optional[date] = None
    publicatiedatum: Optional[date] = None
    einddatum: Optional[date] = None
    resultaat: Optional[str] = None
    relevante_andere_zaken: Optional[List[str]] = None
    zaakgeometrie: Optional[dict] = None


@dataclass
class ZaakType(ZGWModel):
    url: str
    identificatie: str
    omschrijving: str
    vertrouwelijkheidaanduiding: str
    doel: str
    aanleiding: str
    indicatie_intern_of_extern: str
    handeling_initiator: str
    onderwerp: str
    handeling_behandelaar: str
    statustypen: list
    catalogus: Optional[str] = None
    doorlooptijd: Optional[relativedelta] = None
    servicenorm: Optional[relativedelta] = None
    # opschorting_en_aanhouding_mogelijk: bool
    # verlenging_mogelijk: bool
    # publicatie_indicatie: bool
    verlengingstermijn: Optional[relativedelta] = None
    producten_of_diensten: Optional[List[str]] = None
    resultaattypen: Optional[List[str]] = None
    informatieobjecttypen: Optional[List[str]] = None
    roltypen: Optional[List[str]] = None
    besluittypen: Optional[List[str]] = None

    begin_geldigheid: Optional[date] = None
    versiedatum: Optional[date] = None


@dataclass
class ZaakInformatieObject(ZGWModel):
    url: str
    informatieobject: str
    zaak: str
    titel: str
    registratiedatum: datetime
    aard_relatie_weergave: Optional[str] = None
    beschrijving: Optional[str] = None


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
    bestandsnaam: str
    inhoud: str
    bestandsomvang: int
    informatieobjecttype: str
    locked: bool
    beginRegistratie: Optional[datetime] = None
    indicatieGebruiksrecht: Optional[str] = None
    bestandsdelen: Optional[List[str]] = None
    beschrijving: Optional[str] = None
    link: Optional[str] = None
    ontvangstdatum: Optional[str] = None
    verzenddatum: Optional[str] = None
    ondertekening: Optional[dict] = None  # {'soort': '', 'datum': None}
    integriteit: Optional[dict] = None  # {'algoritme': '', 'waarde': '', 'datum': None}


@dataclass
class Rol(ZGWModel):
    url: str
    zaak: str
    betrokkene_type: str
    roltype: str
    omschrijving: str
    omschrijving_generiek: str
    roltoelichting: str
    indicatie_machtiging: Optional[str] = None
    registratiedatum: Optional[datetime] = None
    betrokkene: Optional[str] = None
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
    toelichting: Optional[str] = None


@dataclass
class Status(ZGWModel):
    url: str
    zaak: str
    statustype: str
    datum_status_gezet: Optional[datetime] = None
    statustoelichting: Optional[str] = None
