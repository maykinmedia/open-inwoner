from django.db import models
from django.utils.translation import ugettext_lazy as _

from filer.fields.image import FilerImageField

from open_inwoner.utils.validators import validate_phone_number

from .mixins import GeoModel


class Organization(GeoModel):
    name = models.CharField(
        verbose_name=_("Name"), max_length=250, help_text=_("Name of the organization")
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        max_length=100,
        unique=True,
        help_text=_("Slug of the organization"),
    )
    logo = FilerImageField(
        null=True,
        blank=True,
        verbose_name=_("Logo"),
        on_delete=models.SET_NULL,
        related_name="organization_logos",
        help_text=_("Logo of the organization"),
    )
    type = models.ForeignKey(
        "pdc.OrganizationType",
        verbose_name=_("Type"),
        related_name="organizations",
        on_delete=models.CASCADE,
        help_text=_("Organization type"),
    )
    email = models.EmailField(
        verbose_name=_("Email address"),
        blank=True,
        help_text=_("The email address of the organization"),
    )
    phonenumber = models.CharField(
        verbose_name=_("Phonenumber"),
        blank=True,
        max_length=15,
        validators=[validate_phone_number],
        help_text=_("The phone number of the organization"),
    )
    neighbourhood = models.ForeignKey(
        "pdc.Neighbourhood",
        verbose_name=_("Neighbourhood"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organization",
        help_text=_("The neighbourhood of the organization"),
    )

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    def __str__(self):
        return f"{self.name}"


class OrganizationType(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        unique=True,
        help_text=_("Organization type"),
    )

    class Meta:
        verbose_name = _("Organization type")
        verbose_name_plural = _("Organization types")

    def __str__(self):
        return self.name
