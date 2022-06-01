from typing import List

from drf_spectacular.utils import extend_schema_field
from filer.models import File, Image
from rest_framework import serializers

from open_inwoner.pdc.models import Category, Product, ProductLink, Question, Tag
from open_inwoner.pdc.models.organization import Organization
from open_inwoner.pdc.models.product import (
    ProductCondition,
    ProductFile,
    ProductLocation,
)


class FilerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = (
            "name",
            "description",
            "file",
            "subject_location",
        )


class FilerFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = (
            "name",
            "description",
            "file",
        )


class ProductFileSerializer(serializers.ModelSerializer):
    file = FilerFileSerializer(required=False)

    class Meta:
        model = ProductFile
        fields = ("file",)


class TagSerializer(serializers.ModelSerializer):
    icon = FilerImageSerializer(required=False)
    type = serializers.StringRelatedField()

    class Meta:
        model = Tag
        fields = ("name", "slug", "icon", "type")


class SmallProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = ("url", "name", "slug", "summary")
        extra_kwargs = {
            "url": {"view_name": "api:products-detail", "lookup_field": "slug"},
        }


class Questionserializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("question", "answer")


class SmallCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ("url", "name", "slug", "highlighted", "description")
        extra_kwargs = {
            "url": {"view_name": "api:categories-detail", "lookup_field": "slug"},
        }


class CategoryWithChildSerializer(serializers.ModelSerializer):
    icon = FilerImageSerializer(required=False)
    image = FilerImageSerializer(required=False)
    products = SmallProductSerializer(required=False, many=True)
    questions = Questionserializer(required=False, many=True, source="question_set")
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "name",
            "slug",
            "highlighted",
            "description",
            "icon",
            "image",
            "products",
            "questions",
            "children",
        )

    @extend_schema_field(SmallCategorySerializer(many=True))
    def get_children(self, obj):
        return SmallCategorySerializer(
            obj.get_children(), many=True, context=self._context
        ).data


class OrganizationSerializer(serializers.ModelSerializer):
    logo = FilerImageSerializer(required=False)
    type = serializers.StringRelatedField()
    neighbourhood = serializers.StringRelatedField()

    class Meta:
        model = Organization
        fields = (
            "name",
            "slug",
            "logo",
            "type",
            "email",
            "phonenumber",
            "neighbourhood",
        )


class ProductLocationSerializer(serializers.ModelSerializer):
    coordinates = serializers.SerializerMethodField()

    class Meta:
        model = ProductLocation
        fields = ("name", "street", "housenumber", "postcode", "city", "coordinates")

    @extend_schema_field(List[str])
    def get_coordinates(self, obj):
        return obj.geometry.coords


class ProductConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCondition
        fields = ("name", "question", "positive_text", "negative_text", "rule")


class ProductLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLink
        fields = (
            "name",
            "url",
        )


class ProductSerializer(serializers.ModelSerializer):
    links = ProductLinkSerializer(many=True, required=False)
    categories = SmallCategorySerializer(many=True, required=False)
    related_products = SmallProductSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)
    organizations = OrganizationSerializer(many=True, required=False)
    locations = ProductLocationSerializer(many=True, required=False)
    conditions = ProductConditionSerializer(many=True, required=False)
    files = ProductFileSerializer(many=True, required=False)

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
            "keywords",
            "uniforme_productnaam",
            "locations",
            "conditions",
            "files",
        )
