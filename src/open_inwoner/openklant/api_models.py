import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TypedDict, Union

from zgw_consumers.api_models.base import ZGWModel


class KlantCreateData(TypedDict):
    bronorganisatie: str
    voornaam: str
    voorvoegselAchternaam: str
    achternaam: str
    telefoonnummer: str
    emailadres: str


@dataclass
class Klant(ZGWModel):
    """
    Klanten API
    """

    # eSuite OAS (compatible)
    url: str
    bronorganisatie: str
    klantnummer: str
    website_url: str = ""
    voornaam: str = ""
    voorvoegsel_achternaam: str = ""
    achternaam: str = ""
    telefoonnummer: str = ""
    emailadres: str = ""

    # open-klant OAS
    bedrijfsnaam: str = ""
    functie: str = ""
    adres: Optional[dict] = None
    subject: str = ""
    subject_type: str = ""
    subject_identificatie: Optional[dict] = None

    # open-klant non-standard *AFWIJKING*
    aanmaakkanaal: str = ""
    geverifieerd: bool = False

    def get_name_display(self):
        return " ".join(
            filter(bool, (self.voornaam, self.voorvoegsel_achternaam, self.achternaam))
        )


class MedewerkerIdentificatie(TypedDict):
    identificatie: str
    achternaam: str = ""


class ContactMomentCreateData(TypedDict):
    bronorganisatie: str
    tekst: str
    onderwerp: str
    type: str
    kanaal: str
    medewerkerIdentificatie: MedewerkerIdentificatie


@dataclass
class ContactMoment(ZGWModel):
    """
    Contactmomenten API
    """

    # eSuite OAS (compatible)
    url: str
    bronorganisatie: str
    registratiedatum: Optional[datetime] = None
    kanaal: str = ""
    tekst: str = ""
    # NOTE annoyingly we can't put MedewerkerIdentificatie here as type because of
    medewerker_identificatie: Optional[dict] = None

    # modification to API for eSuite usefulness *AFWIJKING*
    identificatie: str = ""
    type: str = ""
    onderwerp: str = ""
    status: str = ""
    antwoord: str = ""

    # open-klant OAS
    voorkeurskanaal: str = ""
    voorkeurstaal: str = ""
    vorig_contactmoment: Optional[str] = None
    volgend_contactmoment: Optional[str] = None
    onderwerp_links: List[str] = dataclasses.field(default_factory=list)

    initiatiefnemer: str = ""
    medewerker: str = ""

    # open-klant non-standard *AFWIJKING*
    # klantcontactmomenten: Optional[List[str]] = None
    # objectcontactmomenten: Optional[List[str]] = None

    def get_medewerker_display(self):
        mid = self.medewerker_identificatie
        if mid:
            display = " ".join(
                filter(
                    bool,
                    (
                        mid.get("voorletters"),
                        mid.get("voorvoegsel_achternaam"),
                        mid.get("achternaam"),
                    ),
                )
            )
            if display:
                return display
            elif mid.get("identificatie"):
                return mid["identificatie"]
        # default
        return ""


class KlantContactRol:
    BELANGHEBBENDE = "belanghebbende"
    GESPREKSPARTNER = "gesprekspartner"


@dataclass
class KlantContactMoment(ZGWModel):
    """
    Contactmomenten API
    """

    # eSuite OAS (compatible)
    url: str
    contactmoment: Union[str, ContactMoment]
    klant: Union[str, Klant]
    rol: str

    # open-klant non-standard *AFWIJKING*
    gelezen: bool = False
