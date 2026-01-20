from open_inwoner.utils.open_product._resources.base import ResourceMixin
from open_inwoner.utils.open_product.types.pagination import PaginatedResponseBody
from open_inwoner.utils.open_product.types.resources.content_label import (
    ContentLabel,
    ListContentLabelParams,
)


class ContentLabelResource(ResourceMixin):
    """Resource for ContentLabel endpoints."""

    base_path: str = "contentlabels"

    def list(
        self, *, params: ListContentLabelParams | None = None
    ) -> PaginatedResponseBody[ContentLabel]:
        """
        List all content labels with optional filtering.

        Args:
            params: Query parameters for filtering:
                - page: Page number for pagination (optional)

        Returns:
            Paginated response containing content label objects
        """
        response = self._get(self.base_path, params=params)
        response.raise_for_status()
        return response.json()
