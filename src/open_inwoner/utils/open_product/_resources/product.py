import uuid

from open_inwoner.utils.open_product._resources.base import ResourceMixin
from open_inwoner.utils.open_product.types.pagination import PaginatedResponseBody
from open_inwoner.utils.open_product.types.resources.product import (
    ListProductParams,
    Product,
)


class ProductResource(ResourceMixin):
    """Resource for Product endpoints."""

    base_path: str = "producten"

    def list(
        self, *, params: ListProductParams | None = None
    ) -> PaginatedResponseBody[Product]:
        """
        List all products with optional filtering.

        Args:
            params: Query parameters for filtering:
                - naam: Filter by product name (optional)
                - product_type: Filter by product type UUID (optional)
                - page: Page number for pagination (optional)

        Returns:
            Paginated response containing product objects
        """
        response = self._get(self.base_path, params=params)
        response.raise_for_status()
        return response.json()

    def retrieve(
        self,
        /,
        uuid_or_id: str | uuid.UUID | int,
    ) -> Product:
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
