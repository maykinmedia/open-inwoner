from django.db import models
from django.utils.translation import gettext_lazy as _


class LoginTypeChoices(models.TextChoices):
    default = "default", _("E-mail en Wachtwoord")
    digid = "digid", _("DigiD")
    eherkenning = "eherkenning", _("eHerkenning")
    oidc = "oidc", _("OpenId connect")
    eidas_person_bsn = "eidas_person_bsn", _("EIDAS person with BSN")
    eidas_person_pseudo_id = "eidas_person_pseudo_id", _("EIDAS person with Pseudo ID")
    eidas_company = "eidas_company", _("EIDAS company with Company ID")


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
    open = "open", _("Nog te doen")
    approval = "approval", _("Mee bezig")
    closed = "closed", _("Afgerond")


class EmptyStatusChoices(models.TextChoices):
    empty = "", _("Status")
    open = "open", _("Nog te doen")
    approval = "approval", _("Mee bezig")
    closed = "closed", _("Afgerond")


class TypeChoices(models.TextChoices):
    incidental = "incidental", _("Incidentieel")
    recurring = "recurring", _("Terugkerend")


class NotificationChannelChoice(models.TextChoices):
    digital_and_post = "digital_and_post", _("Digitaal en per brief")
    digital_only = "digital_only", _("Alleen digitaal")
