from django.conf import settings

from elasticsearch_dsl import FacetedSearch, NestedFacet, TermsFacet, query

from .constants import FacetChoices
from .documents import ProductDocument
from .models import FieldBoost
from .results import AutocompleteResult, ProductSearchResult


class ProductSearch(FacetedSearch):
    index = settings.ES_INDEX_PRODUCTS
    doc_types = [ProductDocument]
    fields = [
        "name",
        "name.partial",
        "summary",
        "summary.partial",
        "content",
        "content.partial",
        "keywords",
        "keywords.partial",
    ]
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

    def get_boosted_fields(self) -> list:
        """
        Add boosts for particular fields which are configured in the FieldBoost model
        """
        boosted_fields = []
        boost_mapping = FieldBoost.objects.as_dict()

        for field in self.fields:
            boosted_field = (
                f"{field}^{boost_mapping[field]}" if field in boost_mapping else field
            )
            boosted_fields.append(boosted_field)

        return boosted_fields

    def query(self, search, query):
        """
        Add fuzziness and boosting to the default search
        """
        if query:
            fields = self.get_boosted_fields()
            return search.query(
                "multi_match", fields=fields, query=query, fuzziness="AUTO"
            )
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
