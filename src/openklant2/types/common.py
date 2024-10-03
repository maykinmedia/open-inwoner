from typing import Literal, NotRequired, Required

from typing_extensions import TypedDict

# The API uses django-filter, which maps booleans to a BooleanField, of which
# the docs at
# https://django-filter.readthedocs.io/en/stable/ref/widgets.html#booleanwidget
# note:
# This widget converts its input into Python’s True/False values. It will
# convert all case variations of True and False into the internal Python values.
BooleanQueryParam = Literal["True", "False", "true", "false"] | bool


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
