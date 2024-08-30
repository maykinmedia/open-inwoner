from typing import Annotated, Literal, Required

from pydantic import StringConstraints, TypeAdapter
from typing_extensions import NotRequired, TypedDict


class ForeignKeyRef(TypedDict):
    uuid: str
    url: str


class Address(TypedDict):
    nummeraanduidingId: NotRequired[Annotated[str, StringConstraints(max_length=255)]]
    adresregel1: NotRequired[Annotated[str, StringConstraints(max_length=80)]]
    adresregel2: NotRequired[Annotated[str, StringConstraints(max_length=80)]]
    adresregel3: NotRequired[Annotated[str, StringConstraints(max_length=80)]]
    land: NotRequired[Annotated[str, StringConstraints(max_length=4)]]


class ContactName(TypedDict):
    voorletters: NotRequired[str]
    voornaam: NotRequired[str]
    voorvoegselAchternaam: NotRequired[str]
    achternaam: NotRequired[str]


#
# Actoren
#
class ActorListParams(TypedDict):
    actoridentificatorCodeObjecttype: NotRequired[str]
    actoridentificatorCodeObjecttype: NotRequired[str]
    actoridentificatorCodeRegister: NotRequired[str]
    actoridentificatorCodeSoortObjectId: NotRequired[str]
    actoridentificatorObjectId: NotRequired[bool]
    naam: NotRequired[str]
    page: NotRequired[int]
    soortActor: NotRequired[str]


class ActorIdentification(TypedDict):
    objectId: NotRequired[str]
    codeObjecttype: NotRequired[str]
    codeRegister: NotRequired[str]
    codeSoortObjectId: NotRequired[str]


class ActorPayload(TypedDict):
    naam: Required[str]
    soortActor: Required[str]

    indicatieActief: NotRequired[bool]
    actoridentificator: NotRequired[ActorIdentification | None]


class ActorPayloadPartial(TypedDict):
    soortActor: Required[str]

    naam: NotRequired[str]
    indicatieActief: NotRequired[bool]
    actoridentificator: NotRequired[ActorIdentification | None]


class ActorResource(TypedDict):
    uuid: Required[str]
    url: Required[str]
    naam: Required[str]
    soortActor: Required[str]

    indicatieActief: NotRequired[bool]
    actoridentificator: NotRequired[ActorIdentification | None]


ActorPayloadValidator = TypeAdapter(ActorPayload)
ActorPayloadPartialValidator = TypeAdapter(ActorPayloadPartial)


#
# Betrokkenen
#
class BetrokkeneListParams(TypedDict):
    contactnaamAchternaam: NotRequired[str]
    contactnaamVoorletters: NotRequired[str]
    contactnaamVoornaam: NotRequired[str]
    contactnaamVoorvoegselAchternaam: NotRequired[str]
    hadKlantcontact__nummer: NotRequired[str]
    hadKlantcontact__url: NotRequired[str]
    hadKlantcontact__uuid: NotRequired[str]
    organisatienaam: NotRequired[str]
    page: NotRequired[int]
    verstrektedigitaalAdres__adres: NotRequired[str]
    verstrektedigitaalAdres__url: NotRequired[str]
    verstrektedigitaalAdres__uuid: NotRequired[str]
    wasPartij__nummer: NotRequired[str]
    wasPartij__url: NotRequired[str]
    wasPartij__uuid: NotRequired[str]


class BetrokkenePayload(TypedDict):
    wasPartij: Required[ForeignKeyRef | None]
    hadKlantcontact: Required[ForeignKeyRef]
    rol: Required[Literal["vertegenwoordiger", "klant"]]
    initiator: Required[bool]

    bezoekadres: NotRequired[Address | None]
    correspondentieadres: NotRequired[Address | None]
    contactnaam: NotRequired[ContactName | None]
    organisatienaam: NotRequired[str]


class BetrokkenePayloadPartial(TypedDict):
    wasPartij: NotRequired[ForeignKeyRef | None]
    hadKlantcontact: NotRequired[ForeignKeyRef]
    rol: NotRequired[Literal["vertegenwoordiger", "klant"]]
    initiator: NotRequired[bool]
    bezoekadres: NotRequired[Address | None]
    correspondentieadres: NotRequired[Address | None]
    contactnaam: NotRequired[ContactName | None]
    organisatienaam: NotRequired[str]


BetrokkenePayloadValidator = TypeAdapter(BetrokkenePayload)
BetrokkenePayloadPartialValidator = TypeAdapter(BetrokkenePayloadPartial)


class BetrokkeneResource(TypedDict):
    uuid: Required[str]
    url: Required[str]
    wasPartij: Required[ForeignKeyRef]
    hadKlantcontact: Required[ForeignKeyRef]
    digitaleAdresssen: Required[list[ForeignKeyRef]]
    volledigeNaam: Required[str]
    rol: Required[str]
    initiator: Required[bool]

    bezoekadres: NotRequired[Address]
    correspondentieadres: NotRequired[Address]
    contactnaam: NotRequired[ContactName]


BetrokkenePayloadValidator = TypeAdapter(BetrokkenePayload)


#
# Digitale adressen
#
class DigitaalAdresListParams(TypedDict):
    pass


class DigitaalAdresPayload(TypedDict):
    verstrektDoorBetrokkene: Required[bool]
    verstrektDoorPartij: Required[bool]
    soortDigitaalAdres: str
    adres: str
    omschrijving: str


class DigitaalAdresPayloadPartial(TypedDict):
    verstrektDoorBetrokkene: NotRequired[bool]
    verstrektDoorPartij: NotRequired[bool]
    soortDigitaalAdres: NotRequired[str]
    adres: NotRequired[str]
    omschrijving: NotRequired[str]


class DigitaalAdresResource(TypedDict):
    uuid: Required[str]
    url: Required[str]
    verstrektDoorBetrokkene: Required[ForeignKeyRef]
    verstrektDoorPartij: Required[ForeignKeyRef]
    adres: Required[str]
    soortDigitaalAdres: Required[str]
    omschrijving: Required[str]


DigitaalAdresPayloadValidator = TypeAdapter(DigitaalAdresPayload)
DigitaalAdresPayloadPartialValidator = TypeAdapter(DigitaalAdresPayloadPartial)
