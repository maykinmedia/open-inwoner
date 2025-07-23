from typing import Literal, NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict

from openklant2.types.common import Adres, ForeignKeyRef, FullForeigKeyRef

BetrokkeneRol = Literal["vertegenwoordiger", "klant"]


class CreateContactnaam(TypedDict):
    voorletters: str
    voornaam: str
    voorvoegselAchternaam: str
    achternaam: str


class BetrokkeneCreateData(TypedDict):
    wasPartij: ForeignKeyRef
    hadKlantcontact: ForeignKeyRef
    bezoekadres: NotRequired[Adres]
    correspondentieadres: NotRequired[Adres]
    contactnaam: NotRequired[CreateContactnaam]
    rol: BetrokkeneRol
    organisatienaam: str
    initiator: bool


class Betrokkene(TypedDict):
    uuid: str
    url: str
    wasPartij: FullForeigKeyRef
    hadKlantcontact: FullForeigKeyRef
    digitaleAdressen: list[FullForeigKeyRef]
    bezoekadres: Adres
    correspondentieadres: Adres
    contactnaam: CreateContactnaam
    volledigeNaam: str
    rol: BetrokkeneRol
    organisatienaam: str
    initiator: bool


class BetrokkeneRetrieveParams(TypedDict):
    expand: NotRequired[list[Literal["digitaleAdressen",]]]


BetrokkeneCreateDataValidator = TypeAdapter(BetrokkeneCreateData)
BetrokkeneValidator = TypeAdapter(Betrokkene)
