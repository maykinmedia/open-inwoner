from typing import Literal, NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict

#
# Input
#

CodeObjecttype = Literal[
    "natuurlijk_persoon",
    "niet_natuurlijk_persoon",
    "overig",
    "vestiging",
]

CodeSoortObjectId = Literal[
    "bsn",
    "kvk_nummer",
    "overig",
    "rsin",
    "vestigingsnummer",
]

CodeRegister = Literal[
    "brp",
    "hr",
    "overig",
]


class PartijIdentificatorObject(TypedDict):
    codeObjecttype: CodeObjecttype
    codeSoortObjectId: CodeSoortObjectId
    codeRegister: CodeRegister
    objectId: str


class CreateIdentificeerdePartij(TypedDict):
    uuid: str


class CreatePartijIdentificatorData(TypedDict):
    identificeerdePartij: CreateIdentificeerdePartij
    partijIdentificator: PartijIdentificatorObject
    anderePartijIdentificator: NotRequired[str]


class ListPartijIdentificatorenParams(TypedDict, total=False):
    page: int
    partijIdentificatorCodeObjecttype: CodeObjecttype
    partijIdentificatorCodeRegister: CodeRegister
    partijIdentificatorCodeSoortObjectId: CodeSoortObjectId
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
