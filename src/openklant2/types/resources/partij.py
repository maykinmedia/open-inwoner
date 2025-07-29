from typing import Literal, NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict

from openklant2.types.common import Adres, CreateAdres, ForeignKeyRef
from openklant2.types.iso_639_2 import LanguageCode
from openklant2.types.resources.digitaal_adres import DigitaalAdres
from openklant2.types.resources.partij_identificator import (
    CreateEmbeddedPartijIdentificatorData,
)

#
# Input types
#

SoortPartij = Literal["persoon", "contactpersoon", "organisatie"]


class CreateContactnaam(TypedDict):
    voorletters: str
    voornaam: str
    voorvoegselAchternaam: str
    achternaam: str


# Note this is polymorphic, concrete types below
class CreatePartijDataBase(TypedDict):
    soortPartij: Literal["organisatie", "persoon", "contactpersoon"]
    indicatieActief: bool
    nummer: NotRequired[str]
    interneNotitie: NotRequired[str]
    digitaleAdressen: list[ForeignKeyRef] | None
    voorkeursDigitaalAdres: ForeignKeyRef | None
    rekeningnummers: list[ForeignKeyRef] | None
    voorkeursRekeningnummer: ForeignKeyRef | None
    voorkeurstaal: LanguageCode
    indicatieGeheimhouding: bool
    correspondentieadres: NotRequired[CreateAdres]
    bezoekadres: NotRequired[CreateAdres | None]
    partijIdentificatoren: NotRequired[list[CreateEmbeddedPartijIdentificatorData]]


class CreatePartijIdentificatiePersoon(TypedDict):
    contactnaam: CreateContactnaam | None


class CreatePartijIdentificatieContactpersoon(TypedDict):
    contactnaam: CreateContactnaam | None
    werkteVoorPartij: ForeignKeyRef


class CreatePartijIdentificatieOrganisatie(TypedDict):
    naam: str


class CreatePartijPersoonData(CreatePartijDataBase):
    soortPartij: Literal["persoon"]
    partijIdentificatie: CreatePartijIdentificatiePersoon


class CreatePartijContactpersoonData(CreatePartijDataBase):
    soortPartij: Literal["contactpersoon"]
    partijIdentificatie: CreatePartijIdentificatieContactpersoon


class CreatePartijOrganisatieData(CreatePartijDataBase):
    soortPartij: Literal["organisatie"]
    partijIdentificatie: CreatePartijIdentificatieOrganisatie


class PartialUpdatePartijData(CreatePartijDataBase, total=False):
    # TODO: This is required for PATCH, which is a bug. Should be remove when
    # https://github.com/maykinmedia/open-klant/issues/345 is addressed.
    soortPartij: SoortPartij


class PartijListParams(TypedDict, total=False):
    page: int
    vertegenwoordigdePartij__url: str
    partijIdentificator__codeObjecttype: str
    partijIdentificator__codeRegister: str
    partijIdentificator__codeSoortObjectId: str
    partijIdentificator__objectId: str
    soortPartij: Literal["organisatie", "persoon", "contactpersoon"]
    expand: NotRequired[
        list[
            Literal[
                "betrokkenen",
                "betrokkenen.hadKlantcontact",
                "categorieRelaties",
                "digitaleAdressen",
            ]
        ]
    ]


class PartijRetrieveParams(TypedDict):
    expand: NotRequired[
        list[
            Literal[
                "betrokkenen",
                "betrokkenen.hadKlantcontact",
                "categorieRelaties",
                "digitaleAdressen",
            ]
        ]
    ]


#
# Output types
#


class Contactnaam(TypedDict):
    voorletters: str
    voornaam: str
    voorvoegselAchternaam: str
    achternaam: str


class PartijIdentificatiePersoon(TypedDict):
    contactnaam: Contactnaam | None


class PartijIdentificatieOrganisatie(TypedDict):
    naam: str


class PartijIdentificatieContactpersoon(TypedDict):
    contactnaam: Contactnaam | None


class PartijExpand(TypedDict, total=False):
    digitaleAdressen: list[DigitaalAdres]
    # TODO: betrokkenen, categorie_relaties


class Partij(TypedDict):
    uuid: str
    nummer: str
    url: str
    interneNotitie: str
    digitaleAdressen: list[ForeignKeyRef]
    voorkeursDigitaalAdres: ForeignKeyRef | None
    rekeningnummers: list[ForeignKeyRef]
    voorkeursRekeningnummer: ForeignKeyRef | None
    voorkeurstaal: LanguageCode
    indicatieActief: bool
    indicatieGeheimhouding: bool
    correspondentieadres: Adres | None
    bezoekadres: Adres | None
    soortPartij: Literal["organisatie", "persoon", "contactpersoon"]
    partijIdentificatie: (
        PartijIdentificatieContactpersoon
        | PartijIdentificatiePersoon
        | PartijIdentificatieOrganisatie
    )
    _expand: NotRequired[PartijExpand]


#
# Validators
#

PartijValidator = TypeAdapter(Partij)
CreatePartijPersoonDataValidator = TypeAdapter(CreatePartijPersoonData)
CreatePartijOrganisatieDataValidator = TypeAdapter(CreatePartijOrganisatieData)
CreatePartijContactpersoonDataValidator = TypeAdapter(CreatePartijContactpersoonData)
