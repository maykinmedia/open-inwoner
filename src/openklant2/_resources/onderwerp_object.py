import uuid
from typing import cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.onderwerp_object import (
    CreateOnderwerpObjectData,
    OnderwerpObject,
    OnderwerpobjectIdentificatorListParams,
)


class OnderwerpObjectResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "onderwerpobjecten"

    def create(
        self,
        *,
        data: CreateOnderwerpObjectData,
    ) -> OnderwerpObject:
        response = self._post(self.base_path, data=data)
        return cast(OnderwerpObject, self.process_response(response))

    def retrieve(self, /, uuid: str | uuid.UUID) -> OnderwerpObject:
        response = self._get(f"{self.base_path}/{str(uuid)}")
        return cast(OnderwerpObject, self.process_response(response))

    def list(
        self, *, params: OnderwerpobjectIdentificatorListParams | None = None
    ) -> PaginatedResponseBody[OnderwerpObject]:
        response = self._get(f"{self.base_path}", params=params)
        return cast(
            PaginatedResponseBody[OnderwerpObject],
            self.process_response(response),
        )
