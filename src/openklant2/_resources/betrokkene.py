import uuid
from typing import cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.betrokkene import Betrokkene, BetrokkeneCreateData


class BetrokkeneResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "/betrokkenen"

    def create(
        self,
        *,
        data: BetrokkeneCreateData,
    ) -> Betrokkene:
        response = self._post(self.base_path, data=data)
        return cast(Betrokkene, self.process_response(response))

    def retrieve(self, /, uuid: str | uuid.UUID) -> Betrokkene:
        response = self._get(f"{self.base_path}/{str(uuid)}")
        return cast(Betrokkene, self.process_response(response))

    def list(self) -> PaginatedResponseBody[Betrokkene]:
        response = self._get(f"{self.base_path}")
        return cast(
            PaginatedResponseBody[Betrokkene],
            self.process_response(response),
        )
