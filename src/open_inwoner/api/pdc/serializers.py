from django.contrib.sites.models import Site
from django.utils.translation import gettext as _

from filer.models import Image
from rest_framework import serializers

from open_inwoner.pdc.models import (
    Category,
    Product,
    ProductFile,
    ProductLink,
    ProductLocation,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("pk", "name")


class FilerImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = (
            "name",
            "description",
            "file",
            "url",
            "subject_location",
        )

    def get_url(self, obj):
        self.context
        domain = Site.objects.get_current().domain
        return f"{domain}{obj.file.url}"


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


class ProductFileSerializer(serializers.ModelSerializer):
    extension = serializers.SerializerMethodField(
        help_text=_('The file extension (without "." separator). E.g.: "docx"')
    )
    label = serializers.SerializerMethodField(
        help_text=_('The file name (without extension). E.g. "Untitled document".')
    )
    size = serializers.SerializerMethodField(
        help_text=_("The file size in bytes. E.g. 8235")
    )
    url = serializers.SerializerMethodField(
        help_text=_("The absolute url to the file (including scheme, domain and path).")
    )

    class Meta:
        model = ProductFile
        fields = [
            "extension",
            "label",
            "size",
            "url",
        ]

    def get_extension(self, obj):
        return obj.file.extension

    def get_label(self, obj):
        return str(obj.file.label).replace(f".{self.get_extension(obj)}", "")

    def get_size(self, obj):
        return obj.file.file.size

    def get_url(self, obj):
        return self.context["request"].build_absolute_uri(obj.file.file.url)


class ProductLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLink
        fields = (
            "name",
            "url",
        )


class ProductLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLocation
        fields = (
            "city",
            "geometry",
            "housenumber",
            "postcode",
            "name",
            "street",
        )


class ProductSerializer(serializers.ModelSerializer):
    files = ProductFileSerializer(many=True)
    links = ProductLinkSerializer(many=True)
    locations = ProductLocationSerializer(many=True)
    related_products = SmallProductSerializer(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            "categories",
            "content",
            "costs",
            "created_on",
            "link",
            "files",
            "links",
            "locations",
            "name",
            "organizations",
            "related_products",
            "slug",
            "summary",
            "tags",
        )
