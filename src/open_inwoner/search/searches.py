from django.conf import settings

from elasticsearch_dsl import (
    FacetedResponse,
    FacetedSearch,
    NestedFacet,
    TermsFacet,
    query,
)

from open_inwoner.pdc.models import Product

from .constants import FacetChoices
from .documents import ProductDocument


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


def search_products(query_str: str, filters=None) -> FacetedResponse:
    s = ProductSearch(query_str, filters=filters or {})
    result = s.execute()

    # add facets representation for rest api
    facet_groups = []
    for facet_name, facet_buckets in result.facets.to_dict().items():
        model = getattr(Product, facet_name).rel.model
        bucket_keys = [b[0] for b in facet_buckets]
        bucket_mapping = {
            m.slug: m.name for m in model.objects.filter(slug__in=bucket_keys)
        }
        bucket_groups = [
            {
                "slug": b[0],
                "name": bucket_mapping[b[0]],
                "count": b[1],
                "selected": b[2],
            }
            for b in facet_buckets
        ]
        # todo replace empty bucket values with the facet endpoint which shows all buckets
        empty_buckets = [
            {"slug": m.slug, "name": m.name, "count": 0, "selected": False}
            for m in model.objects.exclude(slug__in=bucket_keys).order_by("slug")
        ]
        facet_groups.append(
            {"name": facet_name, "buckets": bucket_groups + empty_buckets}
        )
    result.facet_groups = facet_groups
    return result
