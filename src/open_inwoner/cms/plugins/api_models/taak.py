from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import AnyUrl, BaseModel, ConfigDict, Extra, Field


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class PydanticCamelCaseModel(BaseModel):
    """
    Pydantic BaseModel with alias generator and default config.
    """

    model_config = ConfigDict(
        populate_by_name=True,  # Accept both field name and alias
        alias_generator=to_camel,
        extra=Extra.ignore,
    )


#
# object (generic envelope)
#
class ObjectRecord(PydanticCamelCaseModel):
    index: int
    type_version: int
    data: Optional[dict]
    geometry: Optional[dict]
    start_at: str
    end_at: Optional[str]
    registration_at: str
    correction_for: Optional[int]
    corrected_by: int


class Object(PydanticCamelCaseModel):
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


class Url(PydanticCamelCaseModel):
    model_config = ConfigDict(extra=Extra.forbid)

    uri: AnyUrl


class LegalSubject(PydanticCamelCaseModel):
    identifier: str


class Authorizee(PydanticCamelCaseModel):
    legal_subject: LegalSubject


class Betrokkene(PydanticCamelCaseModel):
    source: Literal["digid", "eherkenning"]
    authorizee: Authorizee
    representee: object | None = None
    level_of_assurance: str
    mandate: object | None = None


class IdentificatieBSN(PydanticCamelCaseModel):
    type: Literal["bsn"]
    value: str = Field(pattern=r"^\d{9}$")


class IdentificatieKVK(PydanticCamelCaseModel):
    type: Literal["kvk"]
    value: str = Field(pattern=r"^\d{8}$")


class KoppelingZaak(PydanticCamelCaseModel):
    model_config = ConfigDict(extra=Extra.forbid)

    registratie: Literal["zaak"]
    value: Optional[UUID] = None


class KoppelingProduct(PydanticCamelCaseModel):
    model_config = ConfigDict(extra=Extra.forbid)

    registratie: Literal["product"]
    value: Optional[UUID] = None


class Formulier(PydanticCamelCaseModel):
    soort: str
    value: str


class Portaalformulier(PydanticCamelCaseModel):
    data: object
    formulier: Formulier
    verzonden_data: object


class TaakUrl(PydanticCamelCaseModel):
    uri: AnyUrl


# Record data models (the actual task data from record.data)
class ExternFormulierTaakRecord(PydanticCamelCaseModel):
    model_config = ConfigDict(extra="forbid")

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


class UrlTaakRecord(PydanticCamelCaseModel):
    model_config = ConfigDict(extra="forbid")

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
    url: TaakUrl


# Object wrapper models (Objects API envelope + record data)
class ExternFormulierTaakObject(PydanticCamelCaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    uuid: str
    record: ExternFormulierTaakRecord


class UrlTaakObject(PydanticCamelCaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    uuid: str
    record: UrlTaakRecord
