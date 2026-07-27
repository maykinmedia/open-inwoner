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
from open_inwoner.utils.html import sanitize_html


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
        fields = ("url", "name", "slug", "published", "summary")
        extra_kwargs = {
            "url": {"view_name": "api:products-detail", "lookup_field": "slug"},
        }


class Questionserializer(serializers.ModelSerializer):
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ("question", "answer")

    def get_answer(self, obj):
        if obj.answer:
            try:
                return sanitize_html(obj.answer.html)
            except Exception:
                return None
        return None


class SmallCategorySerializer(serializers.HyperlinkedModelSerializer):
    description = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("url", "name", "slug", "published", "highlighted", "description")
        extra_kwargs = {
            "url": {"view_name": "api:categories-detail", "lookup_field": "slug"},
        }

    def get_description(self, obj):
        if obj.description:
            try:
                return sanitize_html(obj.description.html)
            except Exception:
                return None
        return None


class CategoryWithChildSerializer(serializers.ModelSerializer):
    icon = FilerImageSerializer(required=False)
    image = FilerImageSerializer(required=False)
    products = SmallProductSerializer(required=False, many=True)
    questions = Questionserializer(required=False, many=True, source="question_set")
    children = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "name",
            "slug",
            "published",
            "highlighted",
            "description",
            "icon",
            "image",
            "products",
            "questions",
            "children",
        )

    def get_description(self, obj):
        if obj.description:
            try:
                return sanitize_html(obj.description.html)
            except Exception:
                return None
        return None

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

    @extend_schema_field(list[str])
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
    content = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "published",
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

    def get_content(self, obj):
        if obj.content:
            try:
                return sanitize_html(obj.content.html)
            except Exception:
                return None
        return None
