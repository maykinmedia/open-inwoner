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
TaakSoort = Literal[
    "ogonebetaling",
    "portaalformulier",
    "url",
    "standaardformulier",
    "externformulier",
    "vrij",
]
TaakStatus = Literal["open", "afgerond", "verwerkt", "gesloten"]


class Url(BaseModel):
    class Config:
        extra = Extra.forbid

    uri: AnyUrl


class LegalSubject(BaseModel):
    identifier: str


class Authorizee(BaseModel):
    legal_subject: LegalSubject


class Betrokkene(BaseModel):
    source: Literal["digid", "eherkenning"]
    authorizee: Authorizee
    representee: object | None = None
    level_of_assurance: str
    mandate: object | None = None


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


class Formulier(BaseModel):
    soort: str
    value: str


class Portaalformulier(BaseModel):
    data: object
    formulier: Formulier
    verzonden_data: object


class TaakUrl(BaseModel):
    uri: AnyUrl


class ExternFormulierTaak(BaseModel):
    # object data
    url: str
    uuid: str

    # record data
    titel: str
    status: TaakStatus
    soort: TaakSoort
    verwerker_taak_id: UUID
    eigenaar: str
    toelichting: str | None = None
    doorlooptijd: str | None = None
    verloopdatum: datetime | None = None
    koppeling: KoppelingZaak | KoppelingProduct | None = None
    betrokkene: Betrokkene
    portaalformulier: Portaalformulier

    class Config:
        extra = Extra.forbid


class UrlTaak(BaseModel):
    # object data
    url: str
    uuid: str

    # record data
    titel: str
    status: TaakStatus
    soort: TaakSoort
    verwerker_taak_id: UUID
    eigenaar: str
    toelichting: str | None = None
    doorlooptijd: str | None = None
    verloopdatum: datetime | None = None
    koppeling: KoppelingZaak | KoppelingProduct | None = None
    identificatie: Union[IdentificatieBSN, IdentificatieKVK]
    task_url: TaakUrl

    class Config:
        extra = Extra.forbid
