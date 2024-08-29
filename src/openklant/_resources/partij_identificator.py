from typing import Optional, TypedDict


class PartijIdentificator(TypedDict):
    codeObjecttype: str
    codeSoortObjectId: str
    objectId: str
    codeRegister: Optional[str]


class IdentificeerdePartij(TypedDict):
    uuid: str

    partijIdentificator: Optional[PartijIdentificator]


class PartijIdentificatorPayload(TypedDict):
    identificeerdePartij: IdentificeerdePartij
    partijIdentificator: PartijIdentificator
    anderePartijIdentificator: Optional[str]  # or not required?
