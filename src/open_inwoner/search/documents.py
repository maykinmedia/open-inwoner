from django.conf import settings

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from open_inwoner.pdc.models import Category, Organization, Product, Tag


@registry.register_document
class ProductDocument(Document):
    slug = fields.KeywordField()

    categories = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
            "description": fields.TextField(),
        }
    )
    tags = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
            "type": fields.TextField(attr="type.name"),
        }
    )
    organizations = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
            "type": fields.TextField(attr="type.name"),
            "neighbourhood": fields.TextField(attr="neighbourhood.name"),
        }
    )

    class Index:
        name = settings.ES_INDEX_PRODUCTS

    class Django:
        model = Product
        fields = ["name", "summary", "content"]
        related_models = [Tag, Organization, Category]

    def get_instances_from_related(self, related_instance):
        return related_instance.products.all()
