from dataclasses import dataclass
from typing import List, Type

from django.db import models

from elasticsearch_dsl import FacetedResponse

from open_inwoner.pdc.models import Product


@dataclass(frozen=True)
class FacetBucket:
    slug: str
    name: str
    count: int = 0
    selected: bool = False

    @property
    def label(self) -> str:
        """display in the label"""
        return f"{self.name} ({self.count})"


@dataclass(init=False)
class Facet:
    name: str
    buckets: List[FacetBucket]
    model: Type[models.Model]

    def __init__(self, name: str, buckets: list, model: models.Model):
        self.name = name
        self.model = model
        self.buckets = self.generate_buckets(buckets)

    def generate_buckets(self, init_buckets: list):
        buckets = []
        for init_bucket in init_buckets:
            if isinstance(init_bucket, FacetBucket):
                buckets.append(init_bucket)
            elif isinstance(init_bucket, tuple) and len(init_bucket) == 3:
                key, count, selected = init_bucket
                buckets.append(
                    FacetBucket(
                        slug=key,
                        name=self.bucket_mapping[key],
                        count=count,
                        selected=selected,
                    )
                )
            else:
                raise NotImplemented("Bucket shape is unknown")

        return buckets

    @property
    def bucket_mapping(self) -> dict:
        if not hasattr(self, "_mapping"):
            self._mapping = {m.slug: m.name for m in self.model.objects.all()}
        return self._mapping

    @property
    def empty_buckets(self) -> List[FacetBucket]:
        if not hasattr(self, "_empty_buckets"):
            bucket_slugs = [b.slug for b in self.buckets]
            empty_queryset = self.model.objects.exclude(slug__in=bucket_slugs).order_by(
                "slug"
            )
            self._empty_buckets = [
                FacetBucket(name=m.name, slug=m.slug) for m in empty_queryset
            ]
        return self._empty_buckets

    @property
    def total_buckets(self) -> List[FacetBucket]:
        return self.buckets + self.empty_buckets

    def choices(self) -> list:
        return [(b.slug, b.label) for b in self.buckets]


@dataclass()
class ProductSearchResult:
    results: list
    facets: list
    _r: FacetedResponse = None

    @classmethod
    def build_from_response(cls, response: FacetedResponse):
        facets = []
        for facet_name, facet_buckets in response.facets.to_dict().items():
            model = getattr(Product, facet_name).rel.model
            facet = Facet(name=facet_name, buckets=facet_buckets, model=model)
            facets.append(facet)

        return cls(results=response.hits, facets=facets, _r=response)
