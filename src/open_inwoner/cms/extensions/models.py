from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.extensions import PageExtension
from cms.extensions.extension_pool import extension_pool


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

    def save(self, *args, **kwargs):
        if self.requires_auth_bsn:
            self.requires_auth = True
        super().save(*args, **kwargs)


extension_pool.register(CommonExtension)
