from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class FacetChoices(DjangoChoices):
    categories = ChoiceItem("categories", _("Filter op onderwerp"))
    tags = ChoiceItem("tags", _("Filter op tags"))
    organizations = ChoiceItem("organizations", _("Filter op organisaties"))
