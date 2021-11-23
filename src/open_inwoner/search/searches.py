from django.conf import settings

from elasticsearch_dsl import FacetedSearch, NestedFacet, TermsFacet, query

from .constants import FacetChoices
from .documents import ProductDocument
from .results import ProductSearchResult


class ProductSearch(FacetedSearch):
    index = settings.ES_INDEX_PRODUCTS
    doc_types = [ProductDocument]
    fields = ["name^4", "summary", "content"]
    facets = {
        FacetChoices.categories: NestedFacet(
            "categories", TermsFacet(field="categories.slug")
        ),
        FacetChoices.tags: NestedFacet("tags", TermsFacet(field="tags.slug")),
        FacetChoices.organizations: NestedFacet(
            "organizations", TermsFacet(field="organizations.slug")
        ),
    }

    def filter(self, search):
        """
        The default FacetedSearch uses post_filter. To avoid confusion rewrite with filter
        """
        if not self._filters:
            return search

        filters = query.MatchAll()
        for f in iter(self._filters.values()):
            filters &= f
        return search.filter(filters)


def search_products(query_str: str, filters=None) -> ProductSearchResult:
    s = ProductSearch(query_str, filters=filters or {})
    response = s.execute()

    return ProductSearchResult.build_from_response(response)
