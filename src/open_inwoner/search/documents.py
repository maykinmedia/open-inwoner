from django.conf import settings

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from open_inwoner.pdc.models import Category, Organization, Product, Tag

from .analyzers import partial_analyzer, synonym_analyzer


@registry.register_document
class ProductDocument(Document):
    name = fields.TextField(
        analyzer="standard",
        search_analyzer=synonym_analyzer,
        fields={
            "raw": fields.KeywordField(),
            "suggest": fields.CompletionField(),
            "partial": fields.TextField(analyzer=partial_analyzer),
        },
    )
    summary = fields.TextField(
        analyzer="standard",
        search_analyzer=synonym_analyzer,
        fields={"partial": fields.TextField(analyzer=partial_analyzer)},
    )
    content = fields.TextField(
        analyzer="standard",
        search_analyzer=synonym_analyzer,
        fields={"partial": fields.TextField(analyzer=partial_analyzer)},
    )
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
    keywords = fields.TextField(
        fields={
            "suggest": fields.CompletionField(multi=True),
            "partial": fields.TextField(multi=True, analyzer=partial_analyzer),
        }
    )

    class Index:
        name = settings.ES_INDEX_PRODUCTS

    class Django:
        model = Product
        related_models = [Tag, Organization, Category]

    def get_instances_from_related(self, related_instance):
        return related_instance.products.all()
