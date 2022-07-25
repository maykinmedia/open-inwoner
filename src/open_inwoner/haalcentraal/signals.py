import logging
from urllib.parse import urljoin

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from glom import PathAccessError, glom
from requests import RequestException
from zds_client import ClientError

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.utils.logentry import system_action

logger = logging.getLogger(__name__)


def fetch_data(instance):
    config = HaalCentraalConfig.get_solo()

    if not config.service:
        logger.warning("no service defined for Haal Centraal")
        return {}

    client = config.service.build_client()
    url = urljoin(client.base_url, "personen")

    try:
        data = client.operation(
            operation_id="GetPersonen",
            url=url,
            data={
                "fields": "naam,geboorte",
                "type": "RaadpleegMetBurgerservicenummer",
                "burgerservicenummer": [instance.bsn],
            },
            request_kwargs=dict(
                headers={"Accept": "application/hal+json"},
            ),
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return {}
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return {}

    return data


@receiver(pre_save, sender=User)
def on_bsn_change(instance, **kwargs):
    if (
        instance.bsn
        and instance.is_prepopulated is False
        and instance.login_type == LoginTypeChoices.digid
    ):
        system_action("Retrieving data from haal centraal based on BSN")
        data = fetch_data(instance)
        if data.get("personen"):
            person = glom(data, "personen")[0]
            try:
                instance.first_name = glom(person, "naam.voornamen")
                instance.last_name = glom(person, "naam.geslachtsnaam")
                instance.birthday = glom(person, "geboorte.datum.datum")
                instance.is_prepopulated = True
            except PathAccessError as e:
                logger.exception(
                    "exception while trying to access fetched data", exc_info=e
                )
            else:
                system_action(_("data was retrieved from haal centraal"), instance)
