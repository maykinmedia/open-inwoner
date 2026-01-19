from typing import Any

from ape_pie import APIClient

from open_inwoner.utils.open_product._resources.product import ProductResource


class ProductClient(APIClient):
    """
    Client for the OpenProduct Product API.

    This client is separate from ProductTypeClient as it may use
    different base URLs and connection parameters.
    """

    product: ProductResource

    def __init__(
        self,
        base_url: str,
        request_kwargs: dict[str, Any] | None = None,
    ):
        super().__init__(base_url=base_url, request_kwargs=request_kwargs)

        self.product = ProductResource(self)
