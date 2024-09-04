import uuid
from typing import cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.digitaal_adres import (
    CreateDigitaalAdresData,
    DigitaalAdres,
    ListDigitaalAdresParams,
)


class DigitaalAdresResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "/digitaleadressen"

    def list(
        self, *, params: ListDigitaalAdresParams | None = None
    ) -> PaginatedResponseBody[DigitaalAdres]:
        response = self._get(self.base_path, params=params)
        return cast(
            PaginatedResponseBody[DigitaalAdres], self.process_response(response)
        )

    def retrieve(self, /, uuid: str | uuid.UUID) -> DigitaalAdres:
        response = self._get(f"{self.base_path}/{str(uuid)}")
        return cast(DigitaalAdres, self.process_response(response))

    def create(
        self,
        *,
        data: CreateDigitaalAdresData,
    ) -> DigitaalAdres:
        response = self._post(self.base_path, data=data)
        return cast(DigitaalAdres, self.process_response(response))
