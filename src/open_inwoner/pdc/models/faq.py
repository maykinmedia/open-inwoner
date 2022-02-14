from django.db import models
from django.utils.translation import ugettext_lazy as _

from ordered_model.models import OrderedModel


class Question(OrderedModel):
    category = models.ForeignKey(
        "pdc.Category", verbose_name=_("category"), on_delete=models.CASCADE
    )
    question = models.CharField(_("Vraag"), max_length=250)
    answer = models.TextField(_("Antwoord"))

    order_with_respect_to = "category"

    class Meta(OrderedModel.Meta):
        verbose_name = _("Vraag")
        verbose_name_plural = _("FAQ vragen")
        ordering = ("category", "order")

    def __str__(self):
        return self.question
