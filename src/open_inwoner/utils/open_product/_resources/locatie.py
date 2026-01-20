import uuid

from open_inwoner.utils.open_product._resources.base import ResourceMixin
from open_inwoner.utils.open_product.types.pagination import PaginatedResponseBody
from open_inwoner.utils.open_product.types.resources.product_type import (
    ListLocatieParams,
    Locatie,
)


class LocatieResource(ResourceMixin):
    """Resource for Locatie endpoints."""

    base_path: str = "locaties"

    def list(
        self, *, params: ListLocatieParams | None = None
    ) -> PaginatedResponseBody[Locatie]:
        """
        List all locaties (locations) with optional filtering.

        Args:
            params: Query parameters for filtering:
                - email__iexact: Filter by exact email (optional)
                - huisnummer__iexact: Filter by exact house number (optional)
                - naam__iexact: Filter by exact name (optional)
                - page: Page number for pagination (optional)
                - page_size: Number of results per page (optional)
                - postcode: Filter by postal code (optional)
                - stad: Filter by city (optional)
                - straat__iexact: Filter by exact street name (optional)
                - telefoonnummer__contains: Filter by phone number containing (optional)

        Returns:
            Paginated response containing locatie objects
        """
        response = self._get(self.base_path, params=params)
        response.raise_for_status()
        return response.json()

    def retrieve(
        self,
        /,
        uuid_or_id: str | uuid.UUID,
    ) -> Locatie:
        """
        Retrieve a single locatie by UUID.

        Args:
            uuid_or_id: The UUID of the locatie

        Returns:
            Locatie object
        """
        response = self._get(f"{self.base_path}/{str(uuid_or_id)}")
        response.raise_for_status()
        return response.json()
