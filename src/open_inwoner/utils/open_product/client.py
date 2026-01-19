import os
from dataclasses import dataclass

from open_inwoner.utils.open_product.product_client import ProductClient
from open_inwoner.utils.open_product.product_type_client import ProductTypeClient


@dataclass(frozen=True)
class OpenProductclient:
    Product: ProductClient
    ProductType: ProductTypeClient

    @classmethod
    def from_token(cls, token: str):
        product_client = ProductClient(
            base_url="https://openproduct.test.maykin.opengem.nl/producten/api/v1/",
            request_kwargs={
                "headers": {
                    "Authorization": f"Token {token}",
                }
            },
        )
        product_type_client = ProductTypeClient(
            base_url="https://openproduct.test.maykin.opengem.nl/producttypen/api/v1/",
            request_kwargs={
                "headers": {
                    "Authorization": f"Token {token}",
                }
            },
        )

        return cls(Product=product_client, ProductType=product_type_client)

    @classmethod
    def from_env(cls):
        return cls.from_token(os.environ["OPENPRODUCT_API_TOKEN"])
