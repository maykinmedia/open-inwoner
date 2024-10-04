import uuid
from typing import Optional, cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.partij import (
    CreatePartijContactpersoonData,
    CreatePartijOrganisatieData,
    CreatePartijPersoonData,
    Partij,
    PartijListParams,
    PartijRetrieveParams,
)


class PartijResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "/partijen"

    def list(
        self, *, params: PartijListParams | None = None
    ) -> PaginatedResponseBody[Partij]:
        response = self._get(self.base_path, params=params)
        return cast(PaginatedResponseBody[Partij], self.process_response(response))

    def retrieve(
        self, /, uuid: str | uuid.UUID, *, params: Optional[PartijRetrieveParams] = None
    ) -> Partij:
        response = self._get(f"{self.base_path}/{str(uuid)}", params=params)
        return cast(Partij, self.process_response(response))

    # Partij is polymorphic on "soortPartij", with varying fields for Persoon, Organisatie and ContactPersoon
    def create_organisatie(self, *, data: CreatePartijOrganisatieData) -> Partij:
        return self._create(data=data)

    def create_persoon(
        self,
        *,
        data: CreatePartijPersoonData,
    ) -> Partij:
        return cast(Partij, self._create(data=data))

    def create_contactpersoon(
        self,
        *,
        data: CreatePartijContactpersoonData,
    ) -> Partij:
        return cast(Partij, self._create(data=data))

    def _create(
        self,
        *,
        data: (
            CreatePartijPersoonData
            | CreatePartijOrganisatieData
            | CreatePartijContactpersoonData
        ),
    ) -> Partij:
        response = self._post(self.base_path, data=data)
        return cast(Partij, self.process_response(response))
