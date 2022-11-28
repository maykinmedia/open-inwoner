from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ordered_model.models import OrderedModel

from open_inwoner.pdc.managers import QuestionQueryset


class Question(OrderedModel):
    category = models.ForeignKey(
        "pdc.Category",
        verbose_name=_("Category"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        "pdc.Product",
        verbose_name=_("Product"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    question = models.CharField(verbose_name=_("Vraag"), max_length=250)
    answer = models.TextField(verbose_name=_("Antwoord"))

    order_with_respect_to = "category"

    objects = QuestionQueryset.as_manager()

    class Meta(OrderedModel.Meta):
        verbose_name = _("Vraag")
        verbose_name_plural = _("FAQ vragen")
        ordering = ("category", "order")

    def clean(self):
        super().clean()
        if self.category and self.product:
            msg = _("A question cannot have both a category and a product")
            raise ValidationError({"category": msg, "product": msg})

    def __str__(self):
        return self.question
