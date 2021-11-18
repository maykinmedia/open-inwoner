from django.conf import settings

from elasticsearch_dsl import FacetedResponse, FacetedSearch, NestedFacet, TermsFacet

from .constants import FacetChoices
from .documents import ProductDocument


class ProductSearch(FacetedSearch):
    index = settings.ES_INDEX_PRODUCTS
    doc_types = [ProductDocument]
    fields = ["name^4", "summary", "content"]
    facets = {
        FacetChoices.categories: NestedFacet(
            "categories", TermsFacet(field="categories.name.raw")
        ),
        FacetChoices.tags: NestedFacet("tags", TermsFacet(field="tags.name.raw")),
        FacetChoices.organizations: NestedFacet(
            "organizations", TermsFacet(field="organizations.name.raw")
        ),
    }


def search_products(query: str, filters=None) -> FacetedResponse:
    s = ProductSearch(query, filters=filters or {})
    result = s.execute()
    # add facets representation for rest api
    result.facet_groups = [
        {"name": k, "buckets": v} for k, v in result.facets.to_dict().items()
    ]
    return result
