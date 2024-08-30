import uuid
from typing import cast

from openklant._resources.base import ResourceMixin

from .types import (
    BetrokkeneListParams,
    BetrokkenePayload,
    BetrokkenePayloadPartial,
    BetrokkeneResource,
)


class Betrokkene(ResourceMixin):
    base_path: str = "/betrokkenen"

    def list(self, *, params: BetrokkeneListParams) -> dict:
        response = self.http_client.get(self.base_path, params=params)
        data = self.process_response(response)
        return data

    def fetch(self, uuid: str | uuid.UUID) -> BetrokkeneResource:
        response = self._get(f"{self.base_path}/{str(uuid)}")

        return cast(BetrokkeneResource, self.process_response(response))

    def create(self, *, data: BetrokkenePayload) -> BetrokkeneResource:
        response = self._post(self.base_path, data=data)

        return cast(BetrokkeneResource, self.process_response(response))

    def update(
        self, uuid: str | uuid.UUID, *, data: BetrokkenePayload
    ) -> BetrokkeneResource:
        response = self._put(f"{self.base_path}/{uuid}", data=data)

        return cast(BetrokkeneResource, self.process_response(response))

    def partial_update(
        self, uuid: str | uuid.UUID, *, data: BetrokkenePayloadPartial
    ) -> BetrokkeneResource:
        response = self._patch(f"{self.base_path}/{uuid}", data=data)

        return cast(BetrokkeneResource, self.process_response(response))
