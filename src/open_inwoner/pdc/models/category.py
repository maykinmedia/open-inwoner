from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from filer.fields.image import FilerImageField
from treebeard.mp_tree import MP_Node


class Category(MP_Node):
    name = models.CharField(
        verbose_name=_("Name"), max_length=100, help_text=_("Name of the category")
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        max_length=100,
        unique=True,
        help_text=_("Slug of the category"),
    )
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        default="",
        help_text=_("Description of the category"),
    )
    icon = FilerImageField(
        verbose_name=_("Icon"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_icons",
        help_text=_("Icon of the category"),
    )
    image = FilerImageField(
        verbose_name=_("Image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_images",
        help_text=_("Image of the category"),
    )

    node_order_by = ["slug"]

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("pdc:category_detail", kwargs={"slug": self.slug})
