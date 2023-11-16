from django.db import models
from django.utils.translation import gettext_lazy as _


class LoginTypeChoices(models.TextChoices):
    default = "default", _("E-mail en Wachtwoord")
    digid = "digid", _("DigiD")
    eherkenning = "eherkenning", _("eHerkenning")
    oidc = "oidc", _("OpenId connect")


# Created because of a filter that needs to happen. This way the form can take the empty choice and the modal is still filled.
class AllEmptyChoice(models.TextChoices):
    empty = "", _("Alle")


class ContactTypeChoices(models.TextChoices):
    contact = "contact", _("Contactpersoon")
    begeleider = "begeleider", _("Begeleider")
    organization = "organization", _("Organisatie")


class EmptyContactTypeChoices(models.TextChoices):
    empty = "", _("Alle")
    contact = "contact", _("Contactpersoon")
    begeleider = "begeleider", _("Begeleider")
    organization = "organization", _("Organisatie")


# Created because of a filter that needs to happen. This way the form can take the empty choice and the modal is still filled.
class StatusEmptyChoice(models.TextChoices):
    empty = "", _("Status")


class StatusChoices(models.TextChoices):
    open = "open", _("Open")
    approval = "approval", _("Accordering")
    closed = "closed", _("Afgerond")

    @staticmethod
    def get_icon_mapping():
        return {
            "open": "format_list_bulleted",
            "approval": "question_mark",
            "closed": "check",
        }

    @classmethod
    def get_icon(cls, status: str, default="label"):
        if status in cls.values:
            icon_mapping = cls.get_icon_mapping()
            return icon_mapping[status]
        else:
            return default

    @classmethod
    def choices_with_icons(cls):
        return [(value, label, cls.get_icon(value)) for value, label in cls.choices]


class EmptyStatusChoices(models.TextChoices):
    empty = "", _("Status")
    open = "open", _("Open")
    approval = "approval", _("Accordering")
    closed = "closed", _("Afgerond")


class TypeChoices(models.TextChoices):
    incidental = "incidental", _("Incidentieel")
    recurring = "recurring", _("Terugkerend")
