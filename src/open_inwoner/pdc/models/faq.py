from django.db import models

from ordered_model.models import OrderedModel


class Question(OrderedModel):
    category = models.ForeignKey("pdc.Category", on_delete=models.CASCADE)
    question = models.CharField("Vraag", max_length=250)
    answer = models.TextField("Antwoord")

    order_with_respect_to = "category"

    class Meta(OrderedModel.Meta):
        verbose_name = "Vraag"
        verbose_name_plural = "FAQ vragen"
        ordering = ("category", "order")

    def __str__(self):
        return self.question
