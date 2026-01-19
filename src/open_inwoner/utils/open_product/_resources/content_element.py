import uuid

from open_inwoner.utils.open_product._resources.base import ResourceMixin
from open_inwoner.utils.open_product.types.pagination import PaginatedResponseBody
from open_inwoner.utils.open_product.types.resources.content_element import (
    ContentElement,
    ListContentElementParams,
)


class ContentElementResource(ResourceMixin):
    """Resource for ContentElement endpoints."""

    base_path: str = "content"

    def list(
        self,
        /,
        product_type_uuid_or_id: str | uuid.UUID | int,
        *,
        params: ListContentElementParams | None = None,
    ) -> PaginatedResponseBody[ContentElement]:
        """
        List all content elements with optional filtering.

        Args:
            params: Query parameters for filtering:
                - labels: Filter by content labels (optional)
                - exclude_labels: Exclude content with certain labels (optional)
                - page: Page number for pagination (optional)

        Returns:
            Paginated response containing content element objects
        """
        response = self._get(
            f"producttypen/{product_type_uuid_or_id}/content", params=params
        )
        response.raise_for_status()
        return response.json()

    def retrieve(
        self,
        /,
        uuid_or_id: str | uuid.UUID | int,
    ) -> ContentElement:
        """
        Retrieve a single content element by UUID or ID.

        Args:
            uuid_or_id: The UUID or ID of the content element

        Returns:
            ContentElement object
        """
        response = self._get(f"{self.base_path}/{str(uuid_or_id)}")
        response.raise_for_status()
        return response.json()
