from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Extra, Field


#
# object (generic envelope)
#
class ObjectRecord(BaseModel):
    index: int
    type_version: int
    data: Optional[dict]
    geometry: Optional[dict]
    start_at: str
    end_at: Optional[str]
    registration_at: str
    correction_for: Optional[int]
    corrected_by: int


class Object(BaseModel):
    url: str
    uuid: str
    type: str
    record: ObjectRecord


#
# taak (object record data)
#
TaakSoort = Literal["ogonebetaling", "portaalformulier", "url"]
TaakStatus = Literal["open", "afgerond", "verwerkt", "gesloten"]


class IdentificatieBSN(BaseModel):
    type: Literal["bsn"]
    value: str = Field(pattern=r"^\d{9}$")


class IdentificatieKVK(BaseModel):
    type: Literal["kvk"]
    value: str = Field(pattern=r"^\d{8}$")


class KoppelingZaak(BaseModel):
    class Config:
        extra = Extra.forbid

    registratie: Literal["zaak"]
    value: Optional[UUID] = None


class KoppelingProduct(BaseModel):
    class Config:
        extra = Extra.forbid

    registratie: Literal["product"]
    value: Optional[UUID] = None


class Url(BaseModel):
    class Config:
        extra = Extra.forbid

    uri: AnyUrl


class TaakUrl(BaseModel):
    uri: AnyUrl


class ObjecttypeTaak(BaseModel):
    class Config:
        extra = Extra.forbid

    titel: str
    status: TaakStatus
    soort: TaakSoort
    verloopdatum: Optional[datetime]
    identificatie: Union[IdentificatieBSN, IdentificatieKVK]
    koppeling: Optional[Union[KoppelingZaak, KoppelingProduct]]
    verwerker_taak_id: UUID
    eigenaar: str
    url: Optional[TaakUrl] = None
