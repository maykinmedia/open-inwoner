from django.db import models
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
