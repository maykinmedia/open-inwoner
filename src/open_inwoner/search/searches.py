import logging

from django.conf import settings

from elasticsearch.dsl import (
    FacetedSearch,
    MultiSearch,
    NestedFacet,
    Q,
    Search,
    TermsFacet,
    query,
)
from elasticsearch.dsl.response import Response

from .constants import FacetChoices
from .documents import CMSPageDocument, ProductDocument
from .models import FieldBoost
from .results import AutocompleteResult, CMSPageSearchResult, ProductSearchResult

logger = logging.getLogger(__name__)


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
            return search.query("multi_match", fields=fields, query=query, fuzziness=0)
        return search

    def faceted_response_from_multi_search_response(self, response: Response):
        """Construct a FacetedResponse from a plain Response returned by MultiSearch."""
        # HACK: Our version of the elasticsearch_dsl library has a bug in MultiSearch:
        # it will not use the `_response_class` defined on the Search object to
        # construct its responses, rather it uses a generic `Response`. This is a
        # problem because we expect the Product search to be a FacetedResponse, and the
        # generic response lacks this information. Fixing this in the library is a bit
        # difficult at this stage, because we're a few versions behind, and we would
        # have to (1) fix this in the official elasticsearch Python library, with which
        # elasticsearch_dsl has now been merged, but that would involved also upgrading
        # our minimal elasticsearch version as well as waiting for django-elasticsearch
        # to support this.
        #
        # Apart from maintaining our own vendored copy, which is something we want to
        # avoid, this is the quickest and cleanest fix.
        products_response = self._s._response_class(
            self._s, response.to_dict(), self._s._doc_type
        )
        products_response._faceted_search = self
        return products_response


def build_cms_search(query_str: str) -> Search:
    """Build a search object targeting the CMS Page index."""
    search = CMSPageDocument.search()
    search = search.query(
        Q(
            "multi_match",
            query=query_str,
            # TODO: Limited to title for now until we have a better sense of what and
            # how to index the CMS pages.
            fields=["title"],
        )
    )
    search = search.highlight(
        "title",
        fragment_size=50,
    )
    return search


def multi_search(
    query_str: str, filters=None
) -> tuple[ProductSearchResult, CMSPageSearchResult]:
    """Execute a search across the Products and CMS Page indexes."""
    product_search = ProductSearch(query_str, filters=filters or {})[
        : settings.ES_MAX_SIZE
    ]
    page_search = build_cms_search(query_str)

    search_query = MultiSearch()
    search_query = search_query.add(search=product_search._s)
    search_query = search_query.add(search=page_search)

    logger.debug("built_search_query: %s", search_query.to_dict())
    products_response, pages_response = search_query.execute()

    return ProductSearchResult.build_from_response(
        response=product_search.faceted_response_from_multi_search_response(
            products_response,
        )
    ), CMSPageSearchResult.build_from_response(pages_response)


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
