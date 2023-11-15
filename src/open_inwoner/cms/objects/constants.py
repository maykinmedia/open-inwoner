from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class StatusChoices(DjangoChoices):
    open = ChoiceItem("open", _("Open"))
    submitted = ChoiceItem("ingediend", _("Submitted"))
    processed = ChoiceItem("verwerkt", _("Processed"))
    closed = ChoiceItem("gesloten", _("Closed"))


class DateOrderChoices(DjangoChoices):
    ascend = ChoiceItem("+", _("Ascend"))
    descent = ChoiceItem("-", _("Descent"))


class ComponentChoices(DjangoChoices):
    link = ChoiceItem("link", _("Link"))
    map = ChoiceItem("map", _("Map"))
