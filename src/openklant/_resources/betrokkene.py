from typing import Annotated, Literal, Optional, Required

from pydantic import StringConstraints, TypeAdapter
from typing_extensions import NotRequired, TypedDict

from openklant._resources.base import ResourceMixin
from openklant.types import HttpAdapter


class ForeignKeyRef(TypedDict):
    uuid: str


class Address(TypedDict):
    nummeraanduidingId: NotRequired[Annotated[str, StringConstraints(max_length=255)]]
    adresregel1: NotRequired[Annotated[str, StringConstraints(max_length=80)]]
    adresregel2: NotRequired[Annotated[str, StringConstraints(max_length=80)]]
    adresregel3: NotRequired[Annotated[str, StringConstraints(max_length=80)]]
    land: NotRequired[Annotated[str, StringConstraints(max_length=4)]]


class ContactName(TypedDict):
    voorletters: NotRequired[str]
    voornaam: NotRequired[str]
    voorvoegselAchternaam: NotRequired[str]
    achternaam: NotRequired[str]


class BetrokkeneCreatePayload(TypedDict):
    wasPartij: ForeignKeyRef
    hadKlantcontact: ForeignKeyRef
    bezoekadres: NotRequired[Address]
    correspondentieadres: NotRequired[Address]
    contactnaam: NotRequired[ContactName]
    rol: Literal["vertegenwoordiger", "klant"]
    organisatienaam: str
    initiator: bool


BetrokkeneCreatePayloadValidator = TypeAdapter(BetrokkeneCreatePayload)


class Betrokkene(ResourceMixin):
    http_client: HttpAdapter
    base_path: str = "/partijen"

    def __init__(self, http_client: HttpAdapter):
        self.http_client = http_client

    def list(self, *, params: Optional[PartijListParams] = None):
        response = self.http_client.get(self.base_path, params=params)
        data = self.process_response(response)
        return data

    def get(
        self, /, uuid: str | uuid.UUID, *, params: Optional[PartijListParams] = None
    ):
        response = self.http_client.get(f"{self.base_path}/{str(uuid)}", params=params)
        data = self.process_response(response)
        return data

    def create_organisatie(self, *, data: CreatePartijOrganisatieData):
        return self._create(data=data)

    def create_persoon(self, *, data: CreatePartijPersoonData):
        return self._create(data=data)

    def _create(
        self,
        *,
        data: CreatePartijPersoonData | CreatePartijOrganisatieData,
    ):
        response = self.http_client.post(f"{self.base_path}/{str(uuid)}", data=data)
        processed_data = self.process_response(response)
        return processed_data
