import uuid
from typing import cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.partij_identificator import (
    CreatePartijIdentificatorData,
    ListPartijIdentificatorenParams,
    PartijIdentificator,
)


class PartijIdentificatorResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "partij-identificatoren"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_iter = self._make_list_iter(self.list)

    def list(
        self, *, params: ListPartijIdentificatorenParams | None = None
    ) -> PaginatedResponseBody[PartijIdentificator]:
        response = self._get(self.base_path, params=params)
        return cast(
            PaginatedResponseBody[PartijIdentificator], self.process_response(response)
        )

    def retrieve(self, /, uuid: str | uuid.UUID) -> PartijIdentificator:
        response = self._get(f"{self.base_path}/{str(uuid)}")
        return cast(PartijIdentificator, self.process_response(response))

    def create(
        self,
        *,
        data: CreatePartijIdentificatorData,
    ) -> PartijIdentificator:
        response = self._post(self.base_path, data=data)
        return cast(PartijIdentificator, self.process_response(response))
