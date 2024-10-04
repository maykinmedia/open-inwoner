import datetime
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from open_inwoner.openproducten.mixins import OpenProductenMixin
from open_inwoner.pdc.models import Product as ProductType


class OpenProductenConfig(SingletonModel):

    producten_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Producten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    class Meta:
        verbose_name = _("Open Producten configuration")


class Price(OpenProductenMixin):
    product_type = models.ForeignKey(
        ProductType,
        verbose_name=_("Product type"),
        on_delete=models.CASCADE,
        related_name="prices",
        help_text=_("The product type that this price belongs to"),
    )
    valid_from = models.DateField(
        verbose_name=_("Start date"),
        validators=[MinValueValidator(datetime.date.today)],
        unique=True,
        help_text=_("The date at which this price is valid"),
    )

    class Meta:
        verbose_name = _("Price")
        verbose_name_plural = _("Prices")
        unique_together = ("product_type", "valid_from")

    def __str__(self):
        return f"{self.product_type.name} {self.valid_from}"


class PriceOption(OpenProductenMixin):
    price = models.ForeignKey(
        Price,
        verbose_name=_("Price"),
        on_delete=models.CASCADE,
        related_name="options",
        help_text=_("The price this option belongs to"),
    )
    amount = models.DecimalField(
        verbose_name=_("Price"),
        decimal_places=2,
        max_digits=8,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("The amount of the price option"),
    )
    description = models.CharField(
        verbose_name=_("Description"),
        max_length=100,
        help_text=_("Short description of the option"),
    )

    class Meta:
        verbose_name = _("Price option")
        verbose_name_plural = _("Price options")

    def __str__(self):
        return f"{self.description} {self.amount}"
