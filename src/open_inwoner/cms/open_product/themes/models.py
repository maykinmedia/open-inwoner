from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from cms.models.fields import PageField


class ThemeList(CMSPlugin):
    title = models.CharField(
        verbose_name=_("Title"), help_text=_("Title of this theme list.")
    )

    def __str__(self):
        return self.title


class Theme(CMSPlugin):
    title = models.CharField(
        verbose_name=_("Title"), help_text=_("Title of this theme.")
    )
    caption = models.CharField(
        verbose_name=_("Caption"),
        help_text="Caption under the title",
        null=True,
        blank=True,
    )
    required_actions = models.BooleanField(
        verbose_name=_("Required actions"),
        help_text=_(
            "Whether the widget should display a 'actions required' indicator."
        ),
        default=False,
    )
    theme_page = PageField(
        verbose_name="Theme Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The page containing the ProductList that this theme should point to.",
    )

    def __str__(self):
        return self.title
