import uuid

from open_inwoner.utils.open_product._resources.base import ResourceMixin
from open_inwoner.utils.open_product.types.pagination import PaginatedResponseBody
from open_inwoner.utils.open_product.types.resources.prijs import (
    ListPrijsParams,
    Prijs,
)


class PrijsResource(ResourceMixin):
    """Resource for Prijs (price) endpoints."""

    base_path: str = "prijzen"

    def list(
        self, *, params: ListPrijsParams | None = None
    ) -> PaginatedResponseBody[Prijs]:
        """
        List all prijzen with optional filtering.

        Args:
            params: Query parameters for filtering:
                - product_type: Filter by product type (optional)
                - product_type__uuid: Filter by product type UUID (optional)
                - product_type__uuid__in: Filter by multiple product type UUIDs (optional)
                - actieve_datum: Filter by exact active date (optional)
                - actieve_datum__gte: Filter by active date greater than or equal (optional)
                - actieve_datum__lte: Filter by active date less than or equal (optional)
                - page: Page number for pagination (optional)

        Returns:
            Paginated response containing prijs objects
        """
        response = self._get(self.base_path, params=params)
        response.raise_for_status()
        return response.json()

    def retrieve(
        self,
        /,
        uuid_or_id: str | uuid.UUID | int,
    ) -> Prijs:
        """
        Retrieve a single prijs by UUID or ID.

        Args:
            uuid_or_id: The UUID or ID of the prijs

        Returns:
            Prijs object
        """
        response = self._get(f"{self.base_path}/{str(uuid_or_id)}")
        response.raise_for_status()
        return response.json()
