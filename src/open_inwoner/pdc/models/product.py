import json
from typing import Union

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from filer.fields.file import FilerFileField

from open_inwoner.utils.validators import validate_phone_number

from .mixins import GeoModel


class Product(models.Model):
    name = models.CharField(
        verbose_name=_("Name"), max_length=100, help_text=_("Name of the product")
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        max_length=100,
        unique=True,
        help_text=_("Slug of the product"),
    )
    summary = models.TextField(
        verbose_name=_("Summary"),
        blank=True,
        default="",
        help_text=_("Short description of the product"),
    )
    link = models.URLField(
        verbose_name=_("Link"),
        blank=True,
        default="",
        help_text=_("Action link to request the product"),
    )
    content = models.TextField(
        verbose_name=_("Content"),
        help_text=_("Product content with build-in WYSIWYG editor"),
    )
    categories = models.ManyToManyField(
        "pdc.Category",
        verbose_name=_("Categories"),
        related_name="products",
        help_text=_("Categories which the product relates to"),
    )
    related_products = models.ManyToManyField(
        "pdc.Product",
        verbose_name=_("Related products"),
        blank=True,
        help_text=_("Related products to this product"),
    )
    tags = models.ManyToManyField(
        "pdc.Tag",
        verbose_name=_("Tags"),
        blank=True,
        related_name="products",
        help_text=_("Tags which the product is linked to"),
    )
    costs = models.DecimalField(
        verbose_name=_("Costs"),
        decimal_places=2,
        max_digits=8,
        default=0,
        help_text=_("Cost of the product in EUR"),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_(
            "This is the date the product was created. This field is automatically set."
        ),
    )
    updated_on = models.DateTimeField(
        verbose_name=_("Updated on"),
        auto_now=True,
        help_text=_(
            "This is the date when the product was last changed. This field is automatically set."
        ),
    )
    organizations = models.ManyToManyField(
        "pdc.Organization",
        verbose_name=_("Organizations"),
        blank=True,
        related_name="products",
        help_text=_("Organizations which provides this product"),
    )
    keywords = ArrayField(
        models.CharField(max_length=100, blank=True),
        verbose_name=_("Keywords"),
        default=list,
        blank=True,
        help_text=_("List of keywords for search"),
    )
    uniforme_productnaam = models.CharField(
        verbose_name=_("Uniforme productnaam"),
        max_length=250,
        blank=True,
        help_text=_("Attribute to sync data from PDC's (like SDG)"),
    )
    conditions = models.ManyToManyField(
        "pdc.ProductCondition",
        related_name="products",
        verbose_name=_("Conditions"),
        blank=True,
        help_text=_("Conditions applicable for the product"),
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("pdc:product_detail", kwargs={"slug": self.slug})


class ProductFile(models.Model):
    product = models.ForeignKey(
        "pdc.Product",
        verbose_name=_("Product"),
        related_name="files",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )
    file = FilerFileField(
        verbose_name=_("File"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_files",
    )

    class Meta:
        verbose_name = _("Product file")
        verbose_name_plural = _("Product files")

    def __str__(self):
        return self.file.name


class ProductContact(models.Model):
    product = models.ForeignKey(
        "pdc.Product",
        verbose_name=_("Product"),
        related_name="product_contacts",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )
    organization = models.ForeignKey(
        "pdc.Organization",
        verbose_name=_("Organization"),
        null=True,
        blank=True,
        related_name="product_contacts",
        on_delete=models.SET_NULL,
        help_text=_("The organization of the product contact"),
    )
    first_name = models.CharField(
        verbose_name=_("First name"),
        max_length=255,
        help_text=_("First name of the product contact"),
    )
    last_name = models.CharField(
        verbose_name=_("Last name"),
        max_length=255,
        help_text=_("Last name of the product contact"),
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
        verbose_name = _("Product contact")
        verbose_name_plural = _("Product contacts")

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
        verbose_name=_("Product"),
        related_name="links",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )
    name = models.CharField(
        verbose_name=_("Name"), max_length=100, help_text=_("Name for the link")
    )
    url = models.URLField(verbose_name=_("Url"), help_text=_("Url of the link"))

    class Meta:
        verbose_name = _("Product link")
        verbose_name_plural = _("Product links")

    def __str__(self):
        return f"{self.product}: {self.name}"


class ProductLocation(GeoModel):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        help_text=_("Location name"),
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        "pdc.Product",
        verbose_name=_("Product"),
        related_name="locations",
        on_delete=models.CASCADE,
        help_text=_("Related product"),
    )

    class Meta:
        verbose_name = _("Product location")
        verbose_name_plural = _("Product locations")

    def __str__(self) -> str:
        return f"{self.product}: {self.address_str}"

    def get_geojson_feature(self, stringify: bool = True) -> Union[str, dict]:
        feature = super().get_geojson_feature(False)
        feature["properties"]["url"] = self.product.get_absolute_url()

        if stringify:
            return json.dumps(feature)
        return feature


class ProductCondition(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        help_text=_("Short name of the condition"),
    )
    question = models.TextField(
        verbose_name=_("Question"),
        help_text=_("Question used in the question-answer game"),
    )
    positive_text = models.TextField(
        verbose_name=_("Positive text"),
        help_text=_("Description how to meet the condition"),
    )
    negative_text = models.TextField(
        verbose_name=_("Negative text"),
        help_text=_("Description how not to meet the condition"),
    )
    rule = models.TextField(
        verbose_name=_("Rule"),
        blank=True,
        default="",
        help_text=_("Rule for the automated check"),
    )

    class Meta:
        verbose_name = _("Condition")
        verbose_name_plural = _("Conditions")

    def __str__(self):
        return self.name
