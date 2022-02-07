from django.db import models
from django.utils.translation import ugettext_lazy as _

from filer.fields.image import FilerImageField

from open_inwoner.utils.validators import validate_phone_number

from .mixins import GeoModel


class Organization(GeoModel):
    name = models.CharField(
        _("name"), max_length=250, help_text=_("Name of the organization")
    )
    slug = models.SlugField(
        _("slug"), max_length=100, unique=True, help_text=_("Slug of the organization")
    )
    logo = FilerImageField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organization_logos",
        help_text=_("Logo of the orgaization"),
    )
    type = models.ForeignKey(
        "pdc.OrganizationType",
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
        max_length=100,
        validators=[validate_phone_number],
        help_text=_("The phone number of the organization"),
    )
    neighbourhood = models.ForeignKey(
        "pdc.Neighbourhood",
        verbose_name=_("neighbourhood"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organization",
        help_text=_("The neighbourhood of the organization"),
    )

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return f"{self.name}"


class OrganizationType(models.Model):
    name = models.CharField(
        _("name"), max_length=100, unique=True, help_text=_("Organization type")
    )

    class Meta:
        verbose_name = _("organization type")
        verbose_name_plural = _("organization types")

    def __str__(self):
        return self.name
