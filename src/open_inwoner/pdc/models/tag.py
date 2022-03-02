from django.db import models
from django.utils.translation import ugettext_lazy as _

from filer.fields.image import FilerImageField


class Tag(models.Model):
    name = models.CharField(
        verbose_name=_("Name"), max_length=100, help_text=_("Name of the tag")
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        max_length=100,
        unique=True,
        help_text=_("Slug of the tag"),
    )
    icon = FilerImageField(
        verbose_name=_("Icon"),
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
        verbose_name=_("Type"),
        on_delete=models.SET_NULL,
        related_name="tags",
        help_text=_("The related tag type"),
    )

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name


class TagType(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        help_text=_("Name of the tag type"),
        unique=True,
    )

    class Meta:
        verbose_name = _("Tag type")
        verbose_name_plural = _("Tag types")

    def __str__(self):
        return self.name
