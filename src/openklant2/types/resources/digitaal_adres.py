from typing import Literal, NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict

from openklant2.types.common import ForeignKeyRef, FullForeigKeyRef

SoortDigitaalAdres = Literal["email", "telefoonnummer", "overig"]


#
# Input
#


class CreateDigitaalAdresData(TypedDict):
    verstrektDoorBetrokkene: ForeignKeyRef | None
    verstrektDoorPartij: ForeignKeyRef | None
    adres: str
    omschrijving: str
    soortDigitaalAdres: SoortDigitaalAdres
    isStandaardAdres: NotRequired[bool]


class ListDigitaalAdresParams(TypedDict):
    page: int


#
# Output
#


class DigitaalAdres(TypedDict):
    verstrektDoorBetrokkene: FullForeigKeyRef | None
    verstrektDoorPartij: FullForeigKeyRef | None
    adres: str
    omschrijving: str
    soortDigitaalAdres: SoortDigitaalAdres
    isStandaardAdres: bool


CreateDigitaalAdresDataValidator = TypeAdapter(CreateDigitaalAdresData)
DigitaalAdresValidator = TypeAdapter(DigitaalAdres)
