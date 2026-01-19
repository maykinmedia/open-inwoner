from typing import Any

from ape_pie import APIClient

from open_inwoner.utils.open_product._resources.content_element import (
    ContentElementResource,
)
from open_inwoner.utils.open_product._resources.content_label import (
    ContentLabelResource,
)
from open_inwoner.utils.open_product._resources.prijs import PrijsResource
from open_inwoner.utils.open_product._resources.product_type import ProductTypeResource
from open_inwoner.utils.open_product._resources.thema import ThemaResource


class ProductTypeClient(APIClient):
    """Client for the OpenProduct ProductType API."""

    thema: ThemaResource
    product_type: ProductTypeResource
    content_element: ContentElementResource
    content_label: ContentLabelResource

    def __init__(
        self,
        base_url: str,
        request_kwargs: dict[str, Any] | None = None,
    ):
        super().__init__(base_url=base_url, request_kwargs=request_kwargs)

        self.thema = ThemaResource(self)
        self.product_type = ProductTypeResource(self)
        self.content_element = ContentElementResource(self)
        self.content_label = ContentLabelResource(self)
        self.prijs = PrijsResource(self)
