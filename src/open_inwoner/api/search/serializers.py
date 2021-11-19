from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from open_inwoner.pdc.models import Product
from open_inwoner.search.constants import FacetChoices


class ProductDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("name", "slug", "summary", "content")


class BucketSerializer(serializers.Serializer):
    slug = serializers.CharField(help_text=_("Slug of the bucket"))
    name = serializers.CharField(help_text=_("Name of the bucket"))
    count = serializers.IntegerField(help_text=_("Number of documents in the bucket"))
    selected = serializers.BooleanField(
        help_text=_("Boolean shows if the bucket value is used in filtering")
    )


class FacetSerializer(serializers.Serializer):
    name = serializers.ChoiceField(
        choices=FacetChoices.choices, help_text=_("Name of the facet")
    )
    buckets = BucketSerializer(many=True, help_text=_("Available buckets"))


class SearchResponseSerializer(serializers.Serializer):
    results = ProductDocumentSerializer(
        many=True, source="hits", help_text=_("List of the search results (hits)")
    )
    facets = FacetSerializer(
        many=True, source="facet_groups", help_text=_("List of available facets")
    )


class SearchQuerySerializer(serializers.Serializer):
    """Serializer used to check query params. Facets are added dynamically"""

    search = serializers.CharField(
        required=False,
        help_text=_("The search string. If empty all the documents are returned."),
    )

    def get_fields(self):
        fields = super().get_fields()

        for facet_name in FacetChoices.values:
            fields[facet_name] = serializers.CharField(
                required=False,
                help_text=_("Value (slug) of the %(facet)s facet")
                % {"facet": facet_name},
            )

        return fields
