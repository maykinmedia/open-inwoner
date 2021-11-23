from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class FacetChoices(DjangoChoices):
    categories = ChoiceItem("categories", _("categories"))
    tags = ChoiceItem("tags", _("tags"))
    organizations = ChoiceItem("organizations", _("organizations"))
