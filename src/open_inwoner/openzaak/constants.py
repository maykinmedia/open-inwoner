from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusIndicators(models.TextChoices):
    info = "info", _("Info")
    warning = "warning", _("Warning")
    failure = "failure", _("Failure")
    success = "success", _("Success")


class ZaakTitleDisplayChoices(models.TextChoices):
    zaak_omschrijving = "zaak_omschrijving", _(
        "The description of the case (`zaak.omschrijving`)"
    )
    zaaktype_omschrijving = "zaaktype_omschrijving", _(
        "The description of the case's type (`zaaktype.omschrijving`)"
    )
    zaaktype_onderwerp = "zaaktype_onderwerp", _(
        "The subject of the case's type (`zaaktype.onderwerp`)"
    )
