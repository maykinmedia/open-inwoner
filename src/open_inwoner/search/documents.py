from django.conf import settings

from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from open_inwoner.pdc.models import Product


@registry.register_document
class ProductDocument(Document):
    class Index:
        name = settings.ES_INDEX_PRODUCTS

    class Django:
        model = Product
        fields = ["name", "summary", "content"]
