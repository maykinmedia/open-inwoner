from django.contrib.gis.db.models import PointField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from filer.fields.image import FilerImageField
from localflavor.nl.models import NLZipCodeField
from treebeard.mp_tree import MP_Node

from .geocode import geocode_address


class Category(MP_Node):
    name = models.CharField(
        _("name"), max_length=100, help_text=_("Name of the category")
    )
    slug = models.SlugField(
        _("slug"), max_length=100, unique=True, help_text=_("Slug of the category")
    )
    description = models.TextField(
        _("description"), blank=True, help_text=_("Description of the category")
    )
    icon = FilerImageField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_icons",
        help_text=_("Icon of the category"),
    )
    image = FilerImageField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_images",
        help_text=_("Image of the category"),
    )

    node_order_by = ["slug"]

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.slug


class Product(models.Model):
    name = models.CharField(
        _("name"), max_length=100, help_text=_("Name of the product")
    )
    summary = models.TextField(
        _("summary"), blank=True, help_text=_("Short description of the product")
    )
    link = models.URLField(
        _("link"), blank=True, help_text=_("Action link to request the product")
    )
    content = models.TextField(
        _("content"), help_text=_("Product content with build-in WYSIWYG editor")
    )
    categories = models.ManyToManyField(
        "pdc.Category",
        related_name="product",
        help_text=_("Categories which the product relates to"),
    )
    related_products = models.ManyToManyField(
        "pdc.Product",
        blank=True,
        help_text=_("Related products to this product"),
    )
    tags = models.ManyToManyField(
        "pdc.Tag",
        blank=True,
        related_name="products",
        help_text=_("Tags which the product is linked to"),
    )
    costs = models.DecimalField(
        _("costs"),
        decimal_places=2,
        max_digits=8,
        default=0,
        help_text=_("Cost of the product in EUR"),
    )
    created_on = models.DateTimeField(
        _("Created on"),
        auto_now_add=True,
        help_text=_(
            "This is the date the product was created. This field is automatically set."
        ),
    )
    updated_on = models.DateTimeField(
        _("Updated on"),
        auto_now=True,
        help_text=_(
            "This is the date when the product was last changed. This field is automatically set."
        ),
    )

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")

    def __str__(self):
        return self.name


class TagType(models.Model):
    name = models.CharField(
        _("name"), max_length=100, help_text=_("Name of the tag type"), unique=True
    )

    class Meta:
        verbose_name = _("tag type")
        verbose_name_plural = _("tag types")

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        _("name"), max_length=100, help_text=_("Name of the tag"), unique=True
    )
    icon = FilerImageField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tag_icons",
        help_text=_("Icon of the tag"),
    )
    type = models.ForeignKey(
        "pdc.TagType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tags",
        help_text=_("The related tag type"),
    )

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tag")

    def __str__(self):
        return self.name


class ProductLink(models.Model):
    product = models.ForeignKey(
        "pdc.Product",
        related_name="links",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )
    name = models.CharField(_("name"), max_length=100, help_text=_("Name for the link"))
    url = models.URLField(_("url"), help_text=_("Url of the link"))

    class Meta:
        verbose_name = _("product link")
        verbose_name_plural = _("product links")

    def __str__(self):
        return f"{self.product}: {self.name}"


class ProductLocation(models.Model):
    product = models.ForeignKey(
        "pdc.Product",
        related_name="locations",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )
    street = models.CharField(
        _("street"), blank=True, max_length=250, help_text=_("Address street")
    )
    housenumber = models.CharField(
        _("house number"),
        blank=True,
        max_length=250,
        help_text=_("Address house number"),
    )
    postcode = NLZipCodeField(_("postcode"), help_text=_("Address postcode"))
    city = models.CharField(_("city"), max_length=250, help_text=_("Address city"))
    geometry = PointField(
        _("geometry"),
        help_text=_("Geo coordinates of the location"),
    )

    class Meta:
        verbose_name = _("product location")
        verbose_name_plural = _("product locations")

    def __str__(self):
        return f"{self.product}: {self.address_str}"

    @property
    def address_str(self):
        # geocoding doesn't work if postcode has space inside
        postcode = self.postcode.replace(" ", "")
        return f"{self.street} {self.housenumber}, {postcode} {self.city}"

    def clean(self):
        super().clean()

        self.clean_geometry()

    def clean_geometry(self):
        # if address is not changed - do nothing
        if (
            self.id
            and self.address_str == ProductLocation.objects.get(id=self.id).address_str
        ):
            return

        # locate geo coordinates using address string
        geometry = geocode_address(self.address_str)
        if not geometry:
            raise ValidationError(
                _(
                    "Geo coordinates of the address can't be found. "
                    "Make sure that the address data are correct"
                )
            )
        self.geometry = geometry
