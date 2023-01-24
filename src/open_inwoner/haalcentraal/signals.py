import logging

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from glom import glom

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
        system_action("Retrieving data from haal centraal based on BSN", user=instance)
        data = fetch_brp_data(instance, brp_version)

        # we have a different response depending on brp version
        if brp_version == "2.0":
            if data.get("personen"):
                data = data.get("personen", [])[0]
            else:
                data = []

        if not data:
            logger.warning("no data retrieved from Haal Centraal")
        else:
            instance.first_name = glom(data, "naam.voornamen", default="")
            instance.last_name = glom(data, "naam.geslachtsnaam", default="")
            instance.birthday = glom(data, "geboorte.datum.datum", default=None)
            instance.street = glom(data, "verblijfplaats.straat", default="")
            instance.housenumber = glom(data, "verblijfplaats.huisnummer", default="")
            instance.city = glom(data, "verblijfplaats.woonplaats", default="")
            instance.is_prepopulated = True

            system_action(_("data was retrieved from haal centraal"), user=instance)
