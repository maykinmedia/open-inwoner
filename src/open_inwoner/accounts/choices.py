from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class LoginTypeChoices(DjangoChoices):
    default = ChoiceItem("default", _("E-mail en Wachtwoord"))
    digid = ChoiceItem("digid", _("DigiD"))
    eherkenning = ChoiceItem("eherkenning", _("eHerkenning"))
    oidc = ChoiceItem("oidc", _("OpenId connect"))


# Created because of a filter that needs to happen. This way the form can take the empty choice and the modal is still filled.
class AllEmptyChoice(DjangoChoices):
    empty = ChoiceItem("", _("Alle"))


class ContactTypeChoices(DjangoChoices):
    contact = ChoiceItem("contact", _("Contactpersoon"))
    begeleider = ChoiceItem("begeleider", _("Begeleider"))
    organization = ChoiceItem("organization", _("Organisatie"))


class EmptyContactTypeChoices(AllEmptyChoice, ContactTypeChoices):
    pass


# Created because of a filter that needs to happen. This way the form can take the empty choice and the modal is still filled.
class StatusEmptyChoice(DjangoChoices):
    empty = ChoiceItem("", _("Status"))


class StatusChoices(DjangoChoices):
    open = ChoiceItem("open", _("Open"))
    closed = ChoiceItem("closed", _("Afgerond"))


class EmptyStatusChoices(StatusEmptyChoice, StatusChoices):
    pass


class TypeChoices(DjangoChoices):
    incidental = ChoiceItem("incidental", _("Incidentieel"))
    recurring = ChoiceItem("recurring", _("Terugkerend"))
