import logging
from sys import exc_info
from urllib.parse import urljoin

from django.db.models.signals import pre_save
from django.dispatch import receiver

from glom import PathAccessError, glom
from requests import RequestException
from zds_client import ClientError

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.haalcentraal.models import HaalCentraalConfig

logger = logging.getLogger(__name__)


def fetch_data(instance):
    config = HaalCentraalConfig.get_solo()

    if not config.service:
        logger.warning("no service defined for Haal Centraal")
        return {}

    client = config.service.build_client()
    url = urljoin(client.base_url, f"ingeschrevenpersonen/{instance.bsn}")
    try:
        data = client.retrieve(
            "ingeschrevenpersonen",
            url=url,
            request_kwargs=dict(
                headers={"Accept": "application/hal+json"},
                params={"fields": "naam,geboorte.datum"},
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
        and instance._old_bsn != instance.bsn
        and instance.login_type == LoginTypeChoices.digid
    ):
        data = fetch_data(instance)
        if data:
            try:
                instance.first_name = glom(data, "naam.voornamen")
                instance.last_name = glom(data, "naam.geslachtsnaam")
                instance.birthday = glom(data, "geboorte.datum.datum")
                instance.is_prepopulated = True
            except PathAccessError as e:
                logger.exception(
                    "exception while trying to access fetched data", exc_info=e
                )
