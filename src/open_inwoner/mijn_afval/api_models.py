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
    totaal_kosten: float


class Periode(PydanticModel):
    eerste_lediging: datetime
    laatste_lediging: datetime


class AfvalContainer(PydanticModel):
    id: str
    afval_type: str
    is_verzamelcontainer: bool
    heeft_sleutel: bool
    totaal_gewicht: float
    totaal_kosten: float


class AfvalContainerLocatie(PydanticModel):
    id: str
    adres: str
    totaal_gewicht: float
    totaal_kosten: float


class AfvalLediging(PydanticModel):
    id: str
    container_location: str
    klant: str
    container: str
    gewicht: float
    geleegd_op: datetime
    kosten: float


class AfvalProfiel(PydanticModel):
    klant: Klant
    containers: list[AfvalContainer]
    container_locaties: list[AfvalContainerLocatie]
    ledigingen: list[AfvalLediging]
