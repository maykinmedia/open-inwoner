from typing import NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict

#
# Input
#


class PartijIdentificatorObject(TypedDict):
    codeObjecttype: str
    codeSoortObjectId: str
    objectId: str
    codeRegister: str


class CreateIdentificeerdePartij(TypedDict):
    uuid: str


class CreatePartijIdentificatorData(TypedDict):
    identificeerdePartij: CreateIdentificeerdePartij
    partijIdentificator: PartijIdentificatorObject
    anderePartijIdentificator: NotRequired[str]


class ListPartijIdentificatorenParams(TypedDict, total=False):
    page: int
    partijIdentificatorCodeObjecttype: str
    partijIdentificatorCodeRegister: str
    partijIdentificatorCodeSoortObjectId: str
    partijIdentificatorObjectId: str


#
# Output
#


class IdentificerendePartij(TypedDict):
    uuid: str
    url: str


class PartijIdentificator(TypedDict):
    identificeerdePartij: IdentificerendePartij
    partijIdentificator: PartijIdentificatorObject
    anderePartijIdentificator: NotRequired[str]


CreatePartijIdentificatorDataValidator = TypeAdapter(CreatePartijIdentificatorData)
PartijIdentificatorValidator = TypeAdapter(PartijIdentificator)
