import logging

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from glom import PathAccessError, glom

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.utils.logentry import system_action

from .utils import fetch_brp_data

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def on_bsn_change(instance, **kwargs):
    brp_version = settings.BRP_VERSION

    if (
        instance.bsn
        and instance.is_prepopulated is False
        and instance.login_type == LoginTypeChoices.digid
    ):
        system_action("Retrieving data from haal centraal based on BSN")

        data = fetch_brp_data(instance, brp_version)

        # we have a different response depending on brp version
        if brp_version == "2.0" and data.get("personen"):
            data = data.get("personen", [])[0]

        try:
            instance.first_name = glom(data, "naam.voornamen")
            instance.last_name = glom(data, "naam.geslachtsnaam")
            instance.birthday = glom(data, "geboorte.datum.datum")
            instance.is_prepopulated = True
        except PathAccessError as e:
            logger.exception(
                "exception while trying to access fetched data", exc_info=e
            )
        else:
            system_action(_("data was retrieved from haal centraal"), instance)
