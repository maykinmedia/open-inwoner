from datetime import datetime

from pydantic import BaseModel, ConfigDict, alias_generators

from .constants import AfvalType


class PydanticModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=alias_generators.to_camel,
    )


class Lediging(PydanticModel):
    tijdstip: datetime
    gewicht: float


class AfvalContainer(PydanticModel):
    identifier: str
    type: AfvalType
    totaal_gewicht: int
    ledigingen: list[Lediging]
    description: str | None = None


class BAGObject(PydanticModel):
    """Basisregistratie Adressen en Gebouwen"""

    object_id: str
    object_address: str
    totaal_gewicht: int
    containers: list[AfvalContainer]
