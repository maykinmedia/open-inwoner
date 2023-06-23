from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Status(DjangoChoices):
    nieuw = ChoiceItem("nieuw", _("Nieuw"))
    in_behandeling = ChoiceItem("in_behandeling", _("In behandeling"))
    afgehandeld = ChoiceItem("afgehandeld", _("Afgehandeld"))

    @classmethod
    def safe_label(cls, value, default=""):
        if not value:
            return default
        try:
            return cls.labels[value]
        except AttributeError:
            if default:
                return default
            return str(value).replace("_", " ").title()
