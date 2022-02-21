import json
from typing import Union

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import markdown
from bs4 import BeautifulSoup
from filer.fields.file import FilerFileField

from open_inwoner.utils.validators import validate_phone_number

from .mixins import GeoModel


class Product(models.Model):
    name = models.CharField(
        _("name"), max_length=100, help_text=_("Name of the product")
    )
    slug = models.SlugField(
        _("slug"), max_length=100, unique=True, help_text=_("Slug of the product")
    )
    summary = models.TextField(
        _("summary"),
        blank=True,
        default="",
        help_text=_("Short description of the product"),
    )
    link = models.URLField(
        _("link"),
        blank=True,
        default="",
        help_text=_("Action link to request the product"),
    )
    content = models.TextField(
        _("content"),
        help_text=_("Product content with build-in WYSIWYG editor"),
    )
    categories = models.ManyToManyField(
        "pdc.Category",
        verbose_name=_("categories"),
        related_name="products",
        help_text=_("Categories which the product relates to"),
    )
    related_products = models.ManyToManyField(
        "pdc.Product",
        verbose_name=_("related products"),
        blank=True,
        help_text=_("Related products to this product"),
    )
    tags = models.ManyToManyField(
        "pdc.Tag",
        verbose_name=_("tags"),
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
    organizations = models.ManyToManyField(
        "pdc.Organization",
        verbose_name=_("organizations"),
        blank=True,
        related_name="products",
        help_text=_("Organizations which provides this product"),
    )
    keywords = ArrayField(
        models.CharField(max_length=100, blank=True),
        verbose_name=_("keywords"),
        default=list,
        blank=True,
        help_text=_("List of keywords for search"),
    )
    uniforme_productnaam = models.CharField(
        _("uniforme productnaam"),
        max_length=250,
        blank=True,
        help_text=_("Attribute to sync data from PDC's (like SDG)"),
    )

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")

    def __str__(self):
        return self.name

    def get_absolute_url(self, category=None):
        if not category:
            return reverse("pdc:product_detail", kwargs={"slug": self.slug})

        category_slug = category.get_build_slug()
        return reverse(
            "pdc:category_product_detail",
            kwargs={"slug": self.slug, "theme_slug": category_slug},
        )

    def get_rendered_content(self):
        md = markdown.Markdown(extensions=["tables"])
        html = md.convert(self.content)
        soup = BeautifulSoup(html, "html.parser")
        class_adders = [
            ("h1", "h1"),
            ("h2", "h2"),
            ("h3", "h3"),
            ("h4", "h4"),
            ("h5", "h5"),
            ("h6", "h6"),
            ("img", "image"),
            ("li", "li"),
            ("p", "p"),
            ("a", "link link--secondary"),
            ("table", "table table--content"),
            ("th", "table__header"),
            ("td", "table__item"),
        ]
        for tag, class_name in class_adders:
            for element in soup.find_all(tag):
                element.attrs["class"] = class_name

        return soup


class ProductFile(models.Model):
    product = models.ForeignKey(
        "pdc.Product",
        related_name="files",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )
    file = FilerFileField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_files",
    )

    class Meta:
        verbose_name = _("product file")
        verbose_name_plural = _("product files")

    def __str__(self):
        return self.file.name


class ProductContact(models.Model):
    product = models.ForeignKey(
        "pdc.Product",
        related_name="product_contacts",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )
    organization = models.ForeignKey(
        "pdc.Organization",
        verbose_name=_("organization"),
        null=True,
        blank=True,
        related_name="product_contacts",
        on_delete=models.SET_NULL,
        help_text=_("The organization of the product contact"),
    )
    first_name = models.CharField(
        _("first name"),
        max_length=255,
        help_text=_("First name of the product contact"),
    )
    last_name = models.CharField(
        _("last name"), max_length=255, help_text=_("Last name of the product contact")
    )
    email = models.EmailField(
        verbose_name=_("Email address"),
        blank=True,
        help_text=_("The email address of the product contact"),
    )
    phonenumber = models.CharField(
        verbose_name=_("Phonenumber"),
        blank=True,
        max_length=100,
        validators=[validate_phone_number],
        help_text=_("The phone number of the product contact"),
    )
    role = models.CharField(
        verbose_name=_("Rol"),
        blank=True,
        max_length=100,
        help_text=_("The role/function of the product contact"),
    )

    class Meta:
        verbose_name = _("product contact")
        verbose_name_plural = _("product contacts")

    def __str__(self):
        return f"{self.product}: {self.first_name} {self.last_name}"

    def get_mailto_link(self):
        email = self.get_email()
        if not email:
            return
        return f"mailto://{email}"

    def get_email(self):
        if self.email:
            return self.email
        return self.organization.email

    def get_phone_number(self):
        if self.phonenumber:
            return self.phonenumber
        return self.organization.phonenumber


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


class ProductLocation(GeoModel):
    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_("Location name"),
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        "pdc.Product",
        related_name="locations",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )

    class Meta:
        verbose_name = _("product location")
        verbose_name_plural = _("product locations")

    def __str__(self) -> str:
        return f"{self.product}: {self.address_str}"

    def get_geojson_feature(self, stringify: bool = True) -> Union[str, dict]:
        feature = super().get_geojson_feature(False)
        feature["properties"]["url"] = self.product.get_absolute_url()

        if stringify:
            return json.dumps(feature)
        return feature
