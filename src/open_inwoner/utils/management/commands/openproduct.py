from django.core.management import BaseCommand

from open_inwoner.utils.open_product.client import OpenProductclient


class Command(BaseCommand):
    help = "Test Open Product integration"

    def handle(self, *args, **options):
        client = OpenProductclient.from_env()

        user_bsn = "111222333"

        producten_for_bsn = client.Product.product.list(
            params={"eigenaren__bsn": "111222333"}
        )

        product_detail = client.Product.product.retrieve(
            "95da2e8a-f657-49e0-8e79-6e8b21f30669"
        )

        themas = client.ProductType.thema.list()
        # TODO
        # locaties = product_type_client.lo
        product_typen_for_thema = client.ProductType.product_type.list(
            params={"themas__uuid": "0ed784aa-ffc0-48d2-8e96-55b3ccfa4ef0"}
        )

        prijzen_voor_product_type = client.ProductType.prijs.list(
            params={"product_type__uuid": "c03b33ce-d2c2-4466-922e-d272bc3633e6"}
        )

        # TODO
        # content_elementen_for_product_type = product_type_client.content_element.list()
