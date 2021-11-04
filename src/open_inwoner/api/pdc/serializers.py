from filer.models import Image
from rest_framework import serializers

from open_inwoner.pdc.models import Category, Product, ProductLink, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("pk", "name")


class FilerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = (
            "name",
            "description",
            "file",
            "subject_location",
        )


class SmallProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = (
            "url",
            "name",
            "slug",
            "summary",
        )
        extra_kwargs = {
            "url": {"view_name": "api:products-detail", "lookup_field": "slug"},
        }


class CategorySerializer(serializers.ModelSerializer):
    product = SmallProductSerializer(many=True, read_only=True)
    image = FilerImageSerializer()

    class Meta:
        model = Category
        fields = (
            "name",
            "slug",
            "description",
            "icon",
            "image",
            "product",
        )


class CategoryWithChildSerializer(CategorySerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "name",
            "slug",
            "description",
            "icon",
            "image",
            "product",
            "children",
        )

    def get_children(self, obj):
        return CategorySerializer(
            obj.get_children(), many=True, context=self._context
        ).data


class ProductLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLink
        fields = (
            "name",
            "url",
        )


class ProductSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    links = ProductLinkSerializer(many=True)
    related_products = SmallProductSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "summary",
            "link",
            "content",
            "categories",
            "related_products",
            "tags",
            "costs",
            "created_on",
            "organizations",
            "links",
        )
