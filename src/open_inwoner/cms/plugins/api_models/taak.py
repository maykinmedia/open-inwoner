from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


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
        extra="ignore",
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
# Status for UrlTaak (Dimpact schema)
TaakStatus = Literal[
    "open",
    "afgerond",
    "verwerkt",
    "gesloten",
]

# Status for ExternFormulierTaak (OIP Klanttaak schema)
ExternFormulierTaakStatus = Literal[
    "open",
    "uitgevoerd",
    "afgebroken",
    "verwerkt",
    "ingetrokken",
]


class Url(PydanticCamelCaseModel):
    model_config = ConfigDict(extra="forbid")

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
    model_config = ConfigDict(extra="forbid")

    registratie: Literal["zaak"]
    value: UUID


class KoppelingProduct(PydanticCamelCaseModel):
    model_config = ConfigDict(extra="forbid")

    registratie: Literal["product"]
    value: UUID


class Formulier(PydanticCamelCaseModel):
    soort: str
    value: str


class Portaalformulier(PydanticCamelCaseModel):
    formulier: Formulier
    data: object | None = None
    verzonden_data: object | None = None


class TaakUrl(PydanticCamelCaseModel):
    uri: AnyUrl


# Record data models (the actual task data from record.data)
class ExternFormulierTaakRecord(PydanticCamelCaseModel):
    model_config = ConfigDict(extra="forbid")

    titel: str
    status: ExternFormulierTaakStatus
    soort: TaakSoort
    verwerker_taak_id: UUID
    eigenaar: str
    betrokkene: Betrokkene
    portaalformulier: Portaalformulier
    toelichting: str | None = None
    doorlooptijd: str | None = Field(None, pattern=r"^P\d+D$")
    verloopdatum: datetime | None = None
    koppeling: KoppelingZaak | KoppelingProduct | None = None
    deadline_verlengbaar: bool | None = None


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
