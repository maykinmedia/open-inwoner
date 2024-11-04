from typing import Literal, NotRequired, Optional, Required

from pydantic import TypeAdapter
from typing_extensions import TypedDict

from openklant2.types.common import BooleanQueryParam, ForeignKeyRef
from openklant2.types.iso_639_2 import LanguageCode


class CreateKlantContactData(TypedDict):
    nummer: NotRequired[str]
    kanaal: str
    onderwerp: str
    inhoud: NotRequired[str]
    indicatieContactGelukt: NotRequired[bool]
    taal: LanguageCode
    vertrouwelijk: bool
    plaatsgevondenOp: NotRequired[str]


class ListKlantContactParams(TypedDict, total=False):
    expand: list[
        Literal[
            "gingOverOnderwerpobjecten",
            "hadBetrokkenen",
            "hadBetrokkenen.digitaleAdressen",
            "hadBetrokkenen.wasPartij",
            "leiddeTotInterneTaken",
            "omvatteBijlagen",
        ]
    ]
    hadBetrokkene__url: str
    hadBetrokkene__uuid: str
    indicatieContactGelukt: BooleanQueryParam
    inhoud: str
    kanaal: str
    nummer: str
    onderwerp: str
    onderwerpobject__onderwerpobjectidentificatorCodeObjecttype: str
    onderwerpobject__onderwerpobjectidentificatorCodeRegister: str
    onderwerpobject__onderwerpobjectidentificatorCodeSoortObjectId: str
    onderwerpobject__onderwerpobjectidentificatorObjectId: str
    onderwerpobject__url: str
    onderwerpobject__uuid: str
    page: int
    plaatsgevondenOp: str
    vertrouwelijk: BooleanQueryParam
    wasOnderwerpobject__onderwerpobjectidentificatorCodeObjecttype: str
    wasOnderwerpobject__onderwerpobjectidentificatorCodeRegister: str
    wasOnderwerpobject__onderwerpobjectidentificatorCodeSoortObjectId: str
    wasOnderwerpobject__onderwerpobjectidentificatorObjectId: str
    wasOnderwerpobject__url: str
    wasOnderwerpobject__uuid: str


class RetrieveKlantContactParams(TypedDict, total=False):
    expand: list[
        Literal[
            "gingOverOnderwerpobjecten",
            "hadBetrokkenen",
            "hadBetrokkenen.digitaleAdressen",
            "hadBetrokkenen.wasPartij",
            "leiddeTotInterneTaken",
            "omvatteBijlagen",
        ]
    ]


class KlantContact(TypedDict):
    uuid: str
    url: str
    # onderwerpobjecten: list[ForeignKeyRef]
    gingOverOnderwerpobjecten: list[ForeignKeyRef]
    hadBetrokkenActoren: list[ForeignKeyRef]  # HAs more
    omvatteBijlagen: list[ForeignKeyRef]
    hadBetrokkenen: list[ForeignKeyRef]
    leiddeTotInterneTaken: list[ForeignKeyRef]

    nummer: str
    kanaal: str
    onderwerp: str
    inhoud: Optional[str]
    indicatieContactGelukt: Required[bool | None]

    taal: LanguageCode
    vertrouwelijk: bool
    plaatsgevondenOp: str


CreateKlantContactDataValidator = TypeAdapter(CreateKlantContactData)
KlantContactValidator = TypeAdapter(KlantContact)
