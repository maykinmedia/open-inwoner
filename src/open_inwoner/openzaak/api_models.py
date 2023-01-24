from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Optional, Union

from zgw_consumers.api_models.base import Model, ZGWModel
from zgw_consumers.api_models.catalogi import (
    InformatieObjectType,
    ResultaatType,
    RolType,
)
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
    zaaktype: Union[str, "ZaakType"]
    registratiedatum: date
    startdatum: date
    vertrouwelijkheidaanduiding: str
    status: Optional[Union[str, "Status"]]
    einddatum_gepland: Optional[date] = None
    uiterlijke_einddatum_afdoening: Optional[date] = None
    #    publicatiedatum: Optional[date]
    einddatum: Optional[date] = None
    resultaat: Optional[str] = None
    #    relevante_andere_zaken: list
    #    zaakgeometrie: dict


@dataclass
class ZaakType(ZGWModel):
    url: str
    # catalogus may be risky on eSuite
    catalogus: str
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

    begin_geldigheid: Optional[date] = None
    einde_geldigheid: Optional[date] = None
    versiedatum: Optional[date] = None
    concept: Optional[bool] = None


@dataclass
class ZaakInformatieObject(ZGWModel):
    url: str
    informatieobject: Union[str, "InformatieObject"]
    zaak: Union[str, Zaak]
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
    # indicatieGebruiksrecht: str
    informatieobjecttype: Union[str, InformatieObjectType]
    locked: bool
    # bestandsdelen: List[str]
    beschrijving: Optional[str] = ""
    link: Optional[str] = ""
    ontvangstdatum: Optional[str] = ""
    verzenddatum: Optional[str] = ""
    ondertekening: Optional[dict] = None  # {'soort': '', 'datum': None}
    integriteit: Optional[dict] = None  # {'algoritme': '', 'waarde': '', 'datum': None}


@dataclass
class Rol(ZGWModel):
    url: str
    zaak: str
    betrokkene_type: str
    roltype: Union[str, RolType]
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
    zaak: Union[str, Zaak]
    resultaattype: Union[str, ResultaatType]
    toelichting: Optional[str] = ""


@dataclass
class StatusType(ZGWModel):
    url: str  # bug: not required according to OAS
    zaaktype: str
    omschrijving: str
    volgnummer: int
    omschrijving_generiek: str = ""
    statustekst: str = ""
    is_eindstatus: bool = False
    # not in eSuite
    informeren: Optional[bool] = False


@dataclass
class Status(ZGWModel):
    url: str
    zaak: Union[str, Zaak]
    statustype: Union[str, StatusType]
    datum_status_gezet: Optional[datetime] = None
    statustoelichting: Optional[str] = ""


@dataclass
class Notification(Model):
    """
    note: not an API response but the data for the Notifications API (NRC) webhook

    {
      "kanaal": "zaken",
      "hoofdObject": "https://test.openzaak.nl/zaken/api/v1/zaken/019a9093-03fe-4121-8423-6c9ab58946ec",
      "resource": "zaak",
      "resourceUrl": "https://test.openzaak.nl/zaken/api/v1/zaken/019a9093-03fe-4121-8423-6c9ab58946ec",
      "actie": "partial_update",
      "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
      "kenmerken": {
        "bronorganisatie": "100000009",
        "zaaktype": "https://test.openzaak.nl/catalogi/api/v1/zaaktypen/53340e34-7581-4b04-884f-8ff7e6a73c2c",
        "vertrouwelijkheidaanduiding": "openbaar"
      }
    }
    """

    kanaal: str
    resource: str
    resource_url: str
    hoofd_object: str
    actie: str
    aanmaakdatum: datetime
    kenmerken: Dict = field(default_factory=dict)
