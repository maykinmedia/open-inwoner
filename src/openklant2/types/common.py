from typing import NotRequired, Required

from typing_extensions import TypedDict


class CreateAdres(TypedDict):
    nummeraanduidingId: Required[str | None]
    adresregel1: NotRequired[str]
    adresregel2: NotRequired[str]
    adresregel3: NotRequired[str]
    land: NotRequired[str]


class Adres(TypedDict):
    nummeraanduidingId: str
    adresregel1: str
    adresregel2: str
    adresregel3: str
    land: str


class ForeignKeyRef(TypedDict):
    uuid: str


class FullForeigKeyRef(TypedDict):
    uuid: str
    url: str
