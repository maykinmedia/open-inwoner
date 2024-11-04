from typing import Literal, NotRequired, Required

from pydantic import TypeAdapter
from typing_extensions import TypedDict

from openklant2.types.common import Adres, CreateAdres, ForeignKeyRef
from openklant2.types.iso_639_2 import LanguageCode
from openklant2.types.resources.digitaal_adres import DigitaalAdres

#
# Input types
#


class CreateContactnaam(TypedDict):
    voorletters: str
    voornaam: str
    voorvoegselAchternaam: str
    achternaam: str


# Note this is polymorphic, concrete types below
class CreatePartijDataBase(TypedDict):
    nummer: NotRequired[str]
    interneNotitie: NotRequired[str]
    digitaleAdressen: Required[list[ForeignKeyRef] | None]
    voorkeursDigitaalAdres: Required[ForeignKeyRef | None]
    rekeningnummers: Required[list[ForeignKeyRef] | None]
    voorkeursRekeningnummer: Required[ForeignKeyRef | None]
    voorkeurstaal: LanguageCode
    indicatieActief: bool
    indicatieGeheimhouding: bool
    correspondentieadres: NotRequired[CreateAdres]
    bezoekadres: NotRequired[CreateAdres | None]


class CreatePartijIdentificatiePersoon(TypedDict):
    contactnaam: Required[CreateContactnaam | None]


class CreatePartijIdentificatieContactpersoon(TypedDict):
    contactnaam: Required[CreateContactnaam | None]
    werkteVoorPartij: ForeignKeyRef


class CreatePartijIdentificatieOrganisatie(TypedDict):
    naam: Required[str]


class CreatePartijPersoonData(CreatePartijDataBase):
    soortPartij: Literal["persoon"]
    partijIdentificatie: CreatePartijIdentificatiePersoon


class CreatePartijContactpersoonData(CreatePartijDataBase):
    soortPartij: Literal["contactpersoon"]
    partijIdentificatie: CreatePartijIdentificatieContactpersoon


class CreatePartijOrganisatieData(CreatePartijDataBase):
    soortPartij: Literal["organisatie"]
    partijIdentificatie: CreatePartijIdentificatieOrganisatie


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
