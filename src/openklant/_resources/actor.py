import uuid
from typing import cast

from openklant._resources.base import ResourceMixin

from .types import ActorListParams, ActorPayload, ActorPayloadPartial, ActorResource


class Actor(ResourceMixin):
    base_path: str = "/actoren"

    def list(self, *, params: ActorListParams) -> dict:
        response = self.http_client.get(self.base_path, params=params)
        data = self.process_response(response)
        return data

    def fetch(self, uuid: str | uuid.UUID) -> ActorResource:
        response = self._get(f"{self.base_path}/{str(uuid)}")

        return cast(ActorResource, self.process_response(response))

    def create(self, *, data: ActorPayload) -> ActorResource:
        response = self._post(self.base_path, data=data)

        return cast(ActorResource, self.process_response(response))

    def update(self, uuid: str | uuid.UUID, *, data: ActorPayload) -> ActorResource:
        response = self._put(f"{self.base_path}/{uuid}", data=data)

        return cast(ActorResource, self.process_response(response))

    def partial_update(
        self, uuid: str | uuid.UUID, *, data: ActorPayloadPartial
    ) -> ActorResource:
        response = self._patch(f"{self.base_path}/{uuid}", data=data)

        return cast(ActorResource, self.process_response(response))
