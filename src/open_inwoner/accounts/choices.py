from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class LoginTypeChoices(DjangoChoices):
    default = ChoiceItem("default", _("Email en Wachtwoord"))
    digid = ChoiceItem("digid", _("DigiD"))
