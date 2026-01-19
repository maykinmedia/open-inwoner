import uuid

from open_inwoner.utils.open_product._resources.base import ResourceMixin
from open_inwoner.utils.open_product.types.pagination import PaginatedResponseBody
from open_inwoner.utils.open_product.types.resources.thema import (
    ListThemaParams,
    Thema,
)


class ThemaResource(ResourceMixin):
    """Resource for Thema (theme) endpoints."""

    base_path: str = "themas"

    def list(
        self, *, params: ListThemaParams | None = None
    ) -> PaginatedResponseBody[Thema]:
        """
        List all themas with optional filtering.

        Args:
            params: Query parameters for filtering:
                - naam: Filter by thema name (optional)
                - parent: Filter by parent thema UUID (optional)
                - page: Page number for pagination (optional)

        Returns:
            Paginated response containing thema objects
        """
        response = self._get(self.base_path, params=params)
        response.raise_for_status()
        return response.json()

    def retrieve(
        self,
        /,
        uuid_or_id: str | uuid.UUID | int,
    ) -> Thema:
        """
        Retrieve a single product by UUID or ID.

        Args:
            uuid_or_id: The UUID or ID of the product

        Returns:
            Product object
        """
        response = self._get(f"{self.base_path}/{str(uuid_or_id)}")
        response.raise_for_status()
        return response.json()
