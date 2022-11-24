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
    open = ChoiceItem("open", _("Open"), icon="format_list_bulleted")
    approval = ChoiceItem("approval", _("Accordering"), icon="question_mark")
    closed = ChoiceItem("closed", _("Afgerond"), icon="check")

    @classmethod
    def get_icon(cls, status, default="label"):
        if status in cls.values:
            return cls.get_choice(status).icon
        else:
            return default

    @classmethod
    def choices_with_icons(cls):
        return [(value, label, cls.get_icon(value)) for value, label in cls.choices]


class EmptyStatusChoices(StatusEmptyChoice, StatusChoices):
    pass


class TypeChoices(DjangoChoices):
    incidental = ChoiceItem("incidental", _("Incidentieel"))
    recurring = ChoiceItem("recurring", _("Terugkerend"))
