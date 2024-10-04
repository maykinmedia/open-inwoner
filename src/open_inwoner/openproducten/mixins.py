from datetime import date

from django.db import models


class OpenProductenMixin(models.Model):
    open_producten_uuid = models.UUIDField(unique=True, editable=False, null=True)

    class Meta:
        abstract = True


class OpenProductenProductTypeMixin(OpenProductenMixin):
    @property
    def current_price(self):
        now = date.today()
        return self.prices.filter(valid_from__lte=now).order_by("valid_from").last()

    class Meta:
        abstract = True
