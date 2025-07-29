from typing import Literal, NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict

from openklant2.types.common import ForeignKeyRef, FullForeigKeyRef

SoortDigitaalAdres = Literal["email", "telefoonnummer", "overig"]


#
# Input
#


class DigitaalAdresCreateData(TypedDict):
    verstrektDoorBetrokkene: ForeignKeyRef | None
    verstrektDoorPartij: ForeignKeyRef | None
    adres: str
    omschrijving: str
    soortDigitaalAdres: SoortDigitaalAdres
    isStandaardAdres: NotRequired[bool]


class ListDigitaalAdresParams(TypedDict):
    page: NotRequired[int]
    verstrektDoorPartij__uuid: NotRequired[str]
    verstrektDoorBetrokkene__uuid: NotRequired[str]


#
# Output
#


class DigitaalAdres(TypedDict):
    uuid: str
    url: str
    verstrektDoorBetrokkene: FullForeigKeyRef | None
    verstrektDoorPartij: FullForeigKeyRef | None
    adres: str
    omschrijving: str
    soortDigitaalAdres: SoortDigitaalAdres
    isStandaardAdres: bool


DigitaalAdresCreateDataValidator = TypeAdapter(DigitaalAdresCreateData)
DigitaalAdresValidator = TypeAdapter(DigitaalAdres)
