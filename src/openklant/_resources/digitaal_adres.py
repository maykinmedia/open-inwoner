import uuid
from typing import cast

from openklant._resources.base import ResourceMixin

from .types import (
    DigitaalAdresListParams,
    DigitaalAdresPayload,
    DigitaalAdresPayloadPartial,
    DigitaalAdresResource,
)


class DigitaalAdres(ResourceMixin):
    base_path: str = "/digitaleadressen"

    def list(self, *, params: DigitaalAdresListParams) -> dict:
        response = self.http_client.get(self.base_path, params=params)
        data = self.process_response(response)
        return data

    def fetch(self, uuid: str | uuid.UUID) -> DigitaalAdresResource:
        response = self._get(f"{self.base_path}/{str(uuid)}")

        return cast(DigitaalAdresResource, self.process_response(response))

    def create(self, *, data: DigitaalAdresPayload) -> DigitaalAdresResource:
        response = self._post(self.base_path, data=data)

        return cast(DigitaalAdresResource, self.process_response(response))

    def update(
        self, uuid: str | uuid.UUID, *, data: DigitaalAdresPayload
    ) -> DigitaalAdresResource:
        response = self._put(f"{self.base_path}/{uuid}", data=data)

        return cast(DigitaalAdresResource, self.process_response(response))

    def partial_update(
        self, uuid: str | uuid.UUID, *, data: DigitaalAdresPayloadPartial
    ) -> DigitaalAdresResource:
        response = self._patch(f"{self.base_path}/{uuid}", data=data)

        return cast(DigitaalAdresResource, self.process_response(response))
