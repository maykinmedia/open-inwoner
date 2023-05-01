from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.extensions import PageExtension
from cms.extensions.extension_pool import extension_pool

from open_inwoner.cms.extensions.constants import Icons, IndicatorChoices


class CommonExtension(PageExtension):
    requires_auth = models.BooleanField(
        _("Requires authentication"),
        default=False,
        help_text=_("Deze pagina vereist een account"),
    )
    requires_auth_bsn = models.BooleanField(
        _("Requires BSN authentication"),
        default=False,
        help_text=_("Deze pagina vereist een account met een Digid BSN"),
    )
    menu_indicator = models.CharField(
        _("Indicator"),
        max_length=32,
        choices=IndicatorChoices.choices,
        blank=True,
        help_text=_("Toon een counter naast het label"),
    )
    menu_icon = models.CharField(
        _("Icon"),
        max_length=32,
        choices=Icons.choices,
        blank=True,
        help_text=_("Icon in het menu"),
    )

    def save(self, *args, **kwargs):
        if self.requires_auth_bsn:
            self.requires_auth = True
        super().save(*args, **kwargs)


extension_pool.register(CommonExtension)
