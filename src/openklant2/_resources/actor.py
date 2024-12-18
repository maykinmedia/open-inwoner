import uuid
from typing import cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.actor import Actor, ActorListParams, CreateActorData


class ActorResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "actoren"

    def create(
        self,
        *,
        data: CreateActorData,
    ) -> Actor:
        response = self._post(self.base_path, data=data)
        return cast(Actor, self.process_response(response))

    def retrieve(self, /, uuid: str | uuid.UUID) -> Actor:
        response = self._get(f"{self.base_path}/{str(uuid)}")
        return cast(Actor, self.process_response(response))

    def list(
        self, *, params: ActorListParams | None = None
    ) -> PaginatedResponseBody[Actor]:
        response = self._get(f"{self.base_path}", params=params)
        return cast(
            PaginatedResponseBody[Actor],
            self.process_response(response),
        )
