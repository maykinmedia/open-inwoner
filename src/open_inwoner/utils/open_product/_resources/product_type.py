import uuid

from open_inwoner.utils.open_product._resources.base import ResourceMixin
from open_inwoner.utils.open_product.types.pagination import PaginatedResponseBody
from open_inwoner.utils.open_product.types.resources.content_element import (
    ListContentElementParams,
    NestedContentElement,
)
from open_inwoner.utils.open_product.types.resources.prijs import ActuelePrijs
from open_inwoner.utils.open_product.types.resources.product_type import (
    ListProductTypeParams,
    ProductType,
)


class ProductTypeResource(ResourceMixin):
    """Resource for ProductType endpoints."""

    base_path: str = "producttypen"

    def list(
        self, *, params: ListProductTypeParams | None = None
    ) -> PaginatedResponseBody[ProductType]:
        """
        List all product types with optional filtering.

        Args:
            params: Query parameters for filtering:
                - naam: Filter by product type name (optional)
                - thema: Filter by thema UUID (optional)
                - page: Page number for pagination (optional)

        Returns:
            Paginated response containing product type objects
        """
        response = self._get(self.base_path, params=params)
        response.raise_for_status()
        return response.json()

    def retrieve(
        self,
        /,
        uuid_or_id: str | uuid.UUID | int,
    ) -> ProductType:
        """
        Retrieve a single product type by UUID or ID.

        Args:
            uuid_or_id: The UUID or ID of the product type

        Returns:
            Product type object
        """
        response = self._get(f"{self.base_path}/{str(uuid_or_id)}")
        response.raise_for_status()
        return response.json()

    def get_content(
        self,
        /,
        uuid_or_id: str | uuid.UUID,
        *,
        params: ListContentElementParams | None = None,
    ) -> PaginatedResponseBody[NestedContentElement]:
        """
        Get all content elements for a specific product type.

        Args:
            uuid_or_id: The UUID or ID of the product type
            params: Query parameters for filtering:
                - labels: Filter by content labels (optional)
                - exclude_labels: Exclude content with certain labels (optional)
                - page: Page number for pagination (optional)

        Returns:
            Paginated response containing content element objects
        """
        response = self._get(
            f"{self.base_path}/{str(uuid_or_id)}/content", params=params
        )
        response.raise_for_status()
        return response.json()

    def get_actuele_prijs(
        self,
        /,
        uuid_or_id: str | uuid.UUID,
    ) -> ActuelePrijs:
        response = self._get(f"{self.base_path}/{str(uuid_or_id)}/actuele-prijs")
        response.raise_for_status()
        return response.json()
