from django.conf import settings

from elasticsearch_dsl import FacetedSearch, NestedFacet, TermsFacet

from .documents import ProductDocument


class ProductSearch(FacetedSearch):
    index = settings.ES_INDEX_PRODUCTS
    doc_types = [ProductDocument]
    fields = ["name^4", "summary", "content"]
    facets = {
        "categories": NestedFacet(
            "categories", TermsFacet(field="categories.name.raw")
        ),
        "tags": NestedFacet("tags", TermsFacet(field="tags.name.raw")),
        "organizations": NestedFacet(
            "organizations", TermsFacet(field="organizations.name.raw")
        ),
    }


def search_products(query: str, filters=None):
    s = ProductSearch(query, filters=filters or {})
    result = s.execute()
    return result.hits
