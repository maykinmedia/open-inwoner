from django.db import models
from django.utils.translation import gettext_lazy as _

from aldryn_apphooks_config.models import AppHookConfig


class ProfileConfig(AppHookConfig):
    my_data = models.BooleanField(
        verbose_name=_("Mijn gegevens"),
        default=True,
        help_text=_(
            "Designates whether 'My data' section is rendered or not (Only for digid users)."
        ),
    )
    mentors = models.BooleanField(
        verbose_name=_("Begeleiders"),
        default=True,
        help_text=_("Designates whether 'mentors' section is rendered or not."),
    )
    my_contacts = models.BooleanField(
        verbose_name=_("Mijn netwerkcontacten"),
        default=True,
        help_text=_("Designates whether 'contacts' section is rendered or not."),
    )
    selfdiagnose = models.BooleanField(
        verbose_name=_("Zelfdiagnose"),
        default=True,
        help_text=_("Designates whether 'self diagnose' section is rendered or not."),
    )
    actions = models.BooleanField(
        verbose_name=_("Acties"),
        default=True,
        help_text=_(
            "Designates whether 'actions' section is rendered or not."
            "If this is disabled, plans (page and menu) should be disabled as well."
        ),
    )
    notifications = models.BooleanField(
        verbose_name=_("Mijn meldingen"),
        default=True,
        help_text=_("Designates whether 'notifications' section is rendered or not."),
    )
    questions = models.BooleanField(
        verbose_name=_("Mijn vragen"),
        default=True,
        help_text=_("Designates whether 'questions' section is rendered or not."),
    )
    ssd = models.BooleanField(
        verbose_name=_("Mijn uitkeringen"),
        default=False,
        help_text=_(
            "Designates whether the 'Mijn uitkeringen' section is rendered or not. "
            "Should only be enabled if a CMS app has been created and the corresponding "
            "CMS page has been published."
        ),
    )
