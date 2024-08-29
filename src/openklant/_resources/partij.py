import uuid
from typing import Literal, NotRequired, Optional, Required, cast

from ape_pie import APIClient
from typing_extensions import TypedDict

from openklant._resources.base import ResourceMixin
from openklant._resources.pagination import PaginatedResponseBody

# TODO: So many types... might be better organized into sub-modules


class ForeignKeyRef(TypedDict):
    uuid: str


class Adres(TypedDict):
    nummeraanduidingId: Required[str | None]
    """Identificatie van het adres bij de Basisregistratie Adressen en Gebouwen."""
    adresregel1: NotRequired[str]
    adresregel2: NotRequired[str]
    adresregel3: NotRequired[str]
    land: NotRequired[str]
    """Een code, opgenomen in Tabel 34, Landentabel, die het land (buiten Nederland) aangeeft alwaar de ingeschrevene verblijft."""


class Contactnaam(TypedDict):
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

    # TODO: ISO 639-2
    voorkeurstaal: str
    indicatieActief: bool
    indicatieGeheimhouding: bool

    correspondentieadres: NotRequired[Adres]
    bezoekadres: NotRequired[Adres]


class PartijIdentificatiePersoon(TypedDict):
    contactnaam: Required[Contactnaam | None]


class PartijIdentificatieContactpersoon(TypedDict):
    contactnaam: Required[Contactnaam]


class PartijIdentificatieOrganisatie(TypedDict):
    contactnaam: Required[Contactnaam | None]


class CreatePartijPersoonData(CreatePartijDataBase):
    soortPartij: Literal["persoon"]
    partijIdentificatie: PartijIdentificatiePersoon


class CreatePartijContactpersoonData(CreatePartijDataBase):
    soortPartij: Literal["contactpersoon"]
    partijIdentificatie: PartijIdentificatieContactpersoon


class CreatePartijOrganisatieData(CreatePartijDataBase):
    soortPartij: Literal["organisatie"]


class PartijResource(TypedDict):
    # TODO: Incomplete!!!
    nummer: NotRequired[str]
    interneNotitie: NotRequired[str]
    digitaleAdressen: Required[list[ForeignKeyRef] | None]
    voorkeursDigitaalAdres: Required[ForeignKeyRef | None]
    rekeningnummers: Required[list[ForeignKeyRef] | None]
    voorkeursRekeningnummer: Required[ForeignKeyRef | None]

    voorkeurstaal: str
    indicatieActief: bool
    indicatieGeheimhouding: bool

    correspondentieadres: NotRequired[Adres]
    bezoekadres: NotRequired[Adres]


class PartijListParams(TypedDict):
    page: NotRequired[int]
    vertegenwoordigdePartij__url: NotRequired[str]


class PartijRetrieveParams(TypedDict):
    expand: NotRequired[
        Literal[
            "betrokkenen",
            "betrokkenen.hadKlantcontact",
            "categorieRelaties",
            "digitaleAdressen",
        ]
    ]


class Partij(ResourceMixin):
    http_client: APIClient
    base_path: str = "/partijen"

    def list(
        self, *, params: Optional[PartijListParams] = None
    ) -> PaginatedResponseBody[PartijResource]:
        response = self._get(self.base_path, params=params)
        return cast(
            PaginatedResponseBody[PartijResource], self.process_response(response)
        )

    def retrieve(
        self, /, uuid: str | uuid.UUID, *, params: Optional[PartijRetrieveParams] = None
    ) -> PartijResource:
        response = self._get(f"{self.base_path}/{str(uuid)}", params=params)
        return cast(PartijResource, self.process_response(response))

    # Partij is polymorphic on "soortPartij", with varying fields for Persoon, Organisatie and ContactPersoon
    def create_organisatie(self, *, data: CreatePartijOrganisatieData):
        return self._create(data=data)

    def create_persoon(
        self,
        *,
        data: CreatePartijPersoonData,
    ) -> PartijResource:
        return cast(PartijResource, self._create(data=data))

    def create_contactpersoon(
        self,
        *,
        data: CreatePartijContactpersoonData,
    ) -> PartijResource:
        return cast(PartijResource, self._create(data=data))

    def _create(
        self,
        *,
        data: (
            CreatePartijPersoonData
            | CreatePartijOrganisatieData
            | CreatePartijContactpersoonData
        ),
    ) -> PartijResource:
        response = self._post(self.base_path, data=data)
        return cast(PartijResource, self.process_response(response))
