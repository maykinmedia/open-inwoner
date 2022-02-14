from django.db import models
from django.utils.translation import ugettext_lazy as _

from filer.fields.image import FilerImageField


class Tag(models.Model):
    name = models.CharField(_("name"), max_length=100, help_text=_("Name of the tag"))
    slug = models.SlugField(
        _("slug"), max_length=100, unique=True, help_text=_("Slug of the tag")
    )
    icon = FilerImageField(
        verbose_name=_("icon"),
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
        verbose_name=_("type"),
        on_delete=models.SET_NULL,
        related_name="tags",
        help_text=_("The related tag type"),
    )

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

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
