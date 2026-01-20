from datetime import datetime

from pydantic import BaseModel, ConfigDict, alias_generators


class PydanticModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=alias_generators.to_camel,
    )


class Klant(PydanticModel):
    id: str
    bsn: str
    naam: str


class Periode(PydanticModel):
    eerste_lediging: datetime
    laatste_lediging: datetime


class Summary(PydanticModel):
    totaal_gewicht: float
    totaal_gewicht_per_afval_type: dict[str, float]
    aantal_ledigingen: int
    aantal_containers: int
    aantal_container_locaties: int
    periode: Periode


class AfvalContainer(PydanticModel):
    id: str
    afval_type: str
    is_verzamelcontainer: bool
    heeft_sleutel: bool
    totaal_gewicht: float


class AfvalContainerLocatie(PydanticModel):
    id: str
    adres: str
    totaal_gewicht: float


class AfvalLediging(PydanticModel):
    id: str
    container_location: str
    klant: str
    container: str
    gewicht: float
    geleegd_op: datetime


class AfvalProfiel(PydanticModel):
    klant: Klant
    summary: Summary
    containers: list[AfvalContainer]
    container_locaties: list[AfvalContainerLocatie]
    ledigingen: list[AfvalLediging]
