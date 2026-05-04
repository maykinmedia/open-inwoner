from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _

from django_prosemirror.fields import ProsemirrorModelField
from django_prosemirror.schema import MarkType, NodeType
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
    answer = ProsemirrorModelField(
        _("Antwoord"),
        allowed_node_types=[
            NodeType.HARD_BREAK,
            NodeType.PARAGRAPH,
            NodeType.HEADING,
            NodeType.BLOCKQUOTE,
            NodeType.TABLE,
            NodeType.TABLE_CELL,
            NodeType.TABLE_HEADER,
            NodeType.TABLE_ROW,
            NodeType.BULLET_LIST,
            NodeType.ORDERED_LIST,
            NodeType.LIST_ITEM,
        ],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.UNDERLINE,
            MarkType.LINK,
        ],
        null=True,
        blank=True,
    )

    order_with_respect_to = "category"

    objects = QuestionQueryset.as_manager()

    class Meta(OrderedModel.Meta):
        verbose_name = _("Vraag")
        verbose_name_plural = _("FAQ vragen")
        ordering = ("category", "order")
        constraints = [
            CheckConstraint(
                check=Q(category__isnull=True) | Q(product__isnull=True),
                name="category_or_product_null",
            ),
        ]

    def clean(self):
        super().clean()
        if self.category and self.product:
            msg = _("A question cannot have both a category and a product")
            raise ValidationError({"category": msg, "product": msg})

    def __str__(self):
        return self.question
