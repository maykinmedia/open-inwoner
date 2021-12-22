from django.conf import settings

from elasticsearch_dsl import FacetedSearch, NestedFacet, TermsFacet, query

from .constants import FacetChoices
from .documents import ProductDocument
from .results import AutocompleteResult, ProductSearchResult


class ProductSearch(FacetedSearch):
    index = settings.ES_INDEX_PRODUCTS
    doc_types = [ProductDocument]
    fields = ["name^4", "summary", "content", "keywords"]
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

    def query(self, search, query):
        """
        Add fuziness to the default search
        """
        if query:
            if self.fields:
                return search.query(
                    "multi_match", fields=self.fields, query=query, fuzziness="AUTO"
                )
            else:
                return search.query("multi_match", query=query, fuzziness="AUTO")
        return search


def search_products(query_str: str, filters=None) -> ProductSearchResult:
    s = ProductSearch(query_str, filters=filters or {})[: settings.ES_MAX_SIZE]
    response = s.execute()

    return ProductSearchResult.build_from_response(response)


def search_autocomplete(query_str: str):
    s = ProductDocument.search()
    completion_params = {
        "size": settings.ES_SUGGEST_SIZE,
        "skip_duplicates": True,
        "fuzzy": True,
    }
    s = s.suggest(
        "name_suggest",
        query_str,
        completion={
            **{"field": "name.suggest"},
            **completion_params,
        },
    )
    s = s.suggest(
        "keyword_suggest",
        query_str,
        completion={**{"field": "keywords.suggest"}, **completion_params},
    )
    response = s.execute()
    return AutocompleteResult.build_from_response(
        response, order=["name_suggest", "keyword_suggest"]
    )
