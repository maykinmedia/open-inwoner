import uuid
from typing import cast

from ape_pie import APIClient

from openklant2._resources.base import ResourceMixin
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.klant_contact import (
    CreateKlantContactData,
    KlantContact,
    ListKlantContactParams,
)


class KlantContactResource(ResourceMixin):
    http_client: APIClient
    base_path: str = "/klantcontacten"

    def create(
        self,
        *,
        data: CreateKlantContactData,
    ) -> KlantContact:
        response = self._post(self.base_path, data=data)
        return cast(KlantContact, self.process_response(response))

    def retrieve(self, /, uuid: str | uuid.UUID) -> KlantContact:
        response = self._get(f"{self.base_path}/{str(uuid)}")
        return cast(KlantContact, self.process_response(response))

    def list(
        self, *, params: ListKlantContactParams | None = None
    ) -> PaginatedResponseBody[KlantContact]:
        response = self._get(f"{self.base_path}", params=params)
        return cast(
            PaginatedResponseBody[KlantContact],
            self.process_response(response),
        )
