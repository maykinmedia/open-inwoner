from django.db import models
from django.db.models.deletion import CASCADE
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField


class Synonym(models.Model):
    term = models.CharField(
        _("term"), max_length=250, unique=True, help_text=_("The term")
    )
    synonyms = ArrayField(
        models.TextField(
            _("synonyms"),
        ),
        help_text=_("Words-synonyms concerning the term"),
    )

    class Meta:
        verbose_name = _("synonym")
        verbose_name_plural = _("synonyms")

    def __str__(self):
        return self.term

    def synonym_line(self) -> str:
        """synonym line in Solr syntax, used for ES"""
        return f"{self.term}, {', '.join(self.synonyms)}"


class Feedback(models.Model):
    search_query = models.CharField(
        verbose_name=_("search query"),
        max_length=250,
        help_text=_("Words which are used by the user in the search box"),
    )
    search_url = models.CharField(
        verbose_name=_("search url"),
        max_length=250,
        blank=True,
        default="",
        help_text=_("The generated url of user's search"),
    )
    positive = models.BooleanField(
        verbose_name=_("positive"),
        help_text=_("Designates whether the feedback was positive or not"),
    )
    remark = models.TextField(
        verbose_name=_("remark"),
        blank=True,
        default="",
        help_text=_(
            "A remark concerning the feedback (positive or negative) that was given"
        ),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_(
            "This is the date the feedback was saved. This field is automatically set"
        ),
    )
    searched_by = models.ForeignKey(
        "accounts.User",
        verbose_name=_("searched by"),
        blank=True,
        null=True,
        on_delete=CASCADE,
        related_name="queries",
        help_text="The logged in user who performed the search",
    )

    def __str__(self):
        return self.search_query

    def get_absolute_url(self):
        return self.search_url
