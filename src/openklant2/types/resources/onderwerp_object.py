from typing import NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict

from openklant2.types.common import ForeignKeyRef, FullForeigKeyRef


class OnderwerpObjectIdentificator(TypedDict):
    objectId: str
    codeObjecttype: str
    codeRegister: str
    codeSoortObjectId: str


class BetrokkeneBase(TypedDict):
    uuid: str
    url: str


class CreateOnderwerpObjectData(TypedDict):
    wasKlantcontact: ForeignKeyRef | None
    klantcontact: ForeignKeyRef | None
    onderwerpobjectidentificator: NotRequired[OnderwerpObjectIdentificator | None]


class OnderwerpObject(TypedDict):
    uuid: str
    url: str
    wasKlantcontact: FullForeigKeyRef | None
    klantcontact: FullForeigKeyRef | None
    onderwerpobjectidentificator: OnderwerpObjectIdentificator


class OnderwerpobjectIdentificatorListParams(TypedDict, total=False):
    onderwerpobjectidentificatorCodeObjecttype: str
    onderwerpobjectidentificatorCodeRegister: str
    onderwerpobjectidentificatorCodeSoortObjectId: str
    onderwerpobjectidentificatorObjectId: str


CreateOnderwerpObjectDataValidator = TypeAdapter(CreateOnderwerpObjectData)
OnderwerpObjectValidator = TypeAdapter(OnderwerpObject)
