from collections import defaultdict

from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import CSPDirective


class CSPSettingQuerySet(models.QuerySet):
    def as_dict(self):
        ret = defaultdict(set)
        for directive, value in self.values_list("directive", "value"):
            ret[directive].add(value)
        return {k: list(v) for k, v in ret.items()}


class CSPSetting(models.Model):
    directive = models.CharField(
        _("directive"),
        max_length=64,
        help_text=_("CSP header directive"),
        choices=CSPDirective.choices,
    )
    value = models.CharField(
        _("value"),
        max_length=128,
        help_text=_("CSP header value"),
    )

    objects = CSPSettingQuerySet.as_manager()

    class Meta:
        ordering = ("directive", "value")

    def __str__(self):
        return f"{self.directive} '{self.value}'"
