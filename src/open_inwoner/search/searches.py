from django.conf import settings

from elasticsearch_dsl import FacetedResponse, FacetedSearch, NestedFacet, TermsFacet

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


def search_products(query: str, filters=None) -> FacetedResponse:
    s = ProductSearch(query, filters=filters or {})
    result = s.execute()

    # add facets representation for rest api
    facet_groups = []
    for facet_name, facet_buckets in result.facets.to_dict().items():
        model = getattr(Product, facet_name).rel.model
        bucket_mapping = {m.slug: m.name for m in model.objects.all()}
        bucket_groups = [
            {"slug": b[0], "name": bucket_mapping[b[0]], "count": b[1]}
            for b in facet_buckets
        ]
        facet_groups.append({"name": facet_name, "buckets": bucket_groups})
    result.facet_groups = facet_groups
    return result
