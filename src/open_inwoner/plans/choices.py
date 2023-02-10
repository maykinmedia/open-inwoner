from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class PlanStatusChoices(DjangoChoices):
    empty = ChoiceItem("", _("Status"))
    open = ChoiceItem("open", _("Open"))
    closed = ChoiceItem("closed", _("Afgerond"))
