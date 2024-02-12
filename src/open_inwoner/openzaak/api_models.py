import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Optional, Union

from dateutil.relativedelta import relativedelta
from zgw_consumers.api_models.base import Model, ZGWModel
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _reformat_esuite_zaak_identificatie(identificatie: str) -> str:
        """
        0014ESUITE66392022 -> 6639-2022

        Static utility function; only used in connection with `Zaak` instances
        """
        exp = r"^\d+ESUITE(?P<num>\d+?)(?P<year>\d{4})$"
        m = re.match(exp, identificatie)
        if not m:
            return identificatie
        num = m.group("num")
        year = m.group("year")
        return f"{num}-{year}"

    def _format_zaak_identificatie(self) -> str:
        from open_inwoner.openzaak.models import OpenZaakConfig

        zaak_config = OpenZaakConfig.get_solo()

        if zaak_config.reformat_esuite_zaak_identificatie:
            return self._reformat_esuite_zaak_identificatie(self.identificatie)
        return self.identificatie

    @property
    def identification(self) -> str:
        return self._format_zaak_identificatie()

    def process_data(self) -> dict:
        """
        Prepare data for template
        """
        from open_inwoner.openzaak.models import StatusTranslation

        status_translate = StatusTranslation.objects.get_lookup()

        return {
            "identification": self.identification,
            "uuid": str(self.uuid),
            "start_date": self.startdatum,
            "end_date": getattr(self, "einddatum", None),
            "description": self.zaaktype.omschrijving,
            "current_status": status_translate.from_glom(
                self, "status.statustype.omschrijving", default=""
            ),
            "zaaktype_config": getattr(self, "zaaktype_config", None),
            "statustype_config": getattr(self, "statustype_config", None),
            "case_type": "Zaak",
        }


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
    # doorlooptijd: relativedelta
    # servicenorm: Optional[relativedelta]
    # opschorting_en_aanhouding_mogelijk: bool
    # verlenging_mogelijk: bool
    # verlengingstermijn: Optional[relativedelta]
    # publicatie_indicatie: bool
    # producten_of_diensten: list
    statustypen: list = None
    resultaattypen: list = None
    informatieobjecttypen: list = field(default_factory=list)
    # roltypen: list
    # besluittypen: list

    # catalogus not on eSuite
    catalogus: str = ""
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
class InformatieObjectType(ZGWModel):
    url: str  # bug: not required according to OAS
    catalogus: str
    omschrijving: str
    vertrouwelijkheidaanduiding: str
    begin_geldigheid: Optional[date] = None
    einde_geldigheid: Optional[date] = None
    concept: bool = False


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
class RolType(ZGWModel):
    url: str  # bug: not required according to OAS
    zaaktype: str
    omschrijving: str
    omschrijving_generiek: str = ""


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
        return RolTypes[self.betrokkene_type].label

    def get_omschrijving_generiek_display(self):
        return RolOmschrijving[self.omschrijving_generiek].label


@dataclass
class ResultaatType(ZGWModel):
    url: str  # bug: not required according to OAS
    zaaktype: str
    omschrijving: str
    resultaattypeomschrijving: str
    selectielijstklasse: str

    omschrijving_generiek: str = ""
    toelichting: str = ""
    archiefnominatie: str = ""
    archiefactietermijn: Optional[relativedelta] = None
    brondatum_archiefprocedure: Optional[dict] = None


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
    volgnummer: Optional[int]  # not in eSuite
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


@dataclass
class OpenSubmission(Model):
    url: str
    uuid: str
    naam: str
    datum_laatste_wijziging: datetime
    vervolg_link: Optional[str] = None
    eind_datum_geldigheid: Optional[datetime] = None

    @property
    def identification(self) -> str:
        return f"{self.naam}: {self.uuid}"

    def process_data(self) -> dict:
        """
        Prepare data for template
        """
        return {
            "identification": self.identification,
            "url": self.url,
            "uuid": self.uuid,
            "naam": self.naam,
            "vervolg_link": self.vervolg_link,
            "datum_laatste_wijziging": self.datum_laatste_wijziging,
            "eind_datum_geldigheid": self.eind_datum_geldigheid or "Geen",
            "case_type": "OpenSubmission",
        }
