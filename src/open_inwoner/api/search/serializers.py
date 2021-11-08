from rest_framework import serializers

from open_inwoner.pdc.models import Product


class ProductDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("name", "slug", "summary", "content")
