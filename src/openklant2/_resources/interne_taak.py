import uuid
from typing import cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.interne_taak import CreateInterneTaakData, InterneTaak


class InterneTaakResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "/internetaken"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_iter = self._make_list_iter(self.list)

    def create(
        self,
        *,
        data: CreateInterneTaakData,
    ) -> InterneTaak:
        response = self._post(self.base_path, data=data)
        return cast(InterneTaak, self.process_response(response))

    def retrieve(self, /, uuid: str | uuid.UUID) -> InterneTaak:
        response = self._get(f"{self.base_path}/{str(uuid)}")
        return cast(InterneTaak, self.process_response(response))

    def list(self) -> PaginatedResponseBody[InterneTaak]:
        response = self._get(f"{self.base_path}")
        return cast(
            PaginatedResponseBody[InterneTaak],
            self.process_response(response),
        )
