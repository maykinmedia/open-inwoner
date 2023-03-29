import logging
from datetime import datetime
from urllib.parse import urljoin

from django.utils.translation import gettext as _

from glom import glom
from requests import RequestException
from zds_client import ClientError

from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.utils.logentry import system_action

logger = logging.getLogger(__name__)


def fetch_brp_data(instance, brp_version):
    config = HaalCentraalConfig.get_solo()

    if not config.service:
        logger.warning("no service defined for Haal Centraal")
        return {}

    client = config.service.build_client()

    data = {}
    if brp_version == "2.0":
        url = urljoin(client.base_url, "personen")
        try:
            data = client.operation(
                operation_id="GetPersonen",
                url=url,
                data={
                    "fields": "geslachtsaanduiding,naam,geboorte,verblijfplaats",
                    "type": "RaadpleegMetBurgerservicenummer",
                    "burgerservicenummer": [instance.bsn],
                },
                request_kwargs=dict(
                    headers={"Accept": "application/json"}, verify=False
                ),
            )
        except RequestException as e:
            logger.exception("exception while making request", exc_info=e)
            return {}
        except ClientError as e:
            logger.exception("exception while making request", exc_info=e)
            return {}

    elif brp_version == "1.3":
        url = urljoin(client.base_url, f"ingeschrevenpersonen/{instance.bsn}")
        try:
            headers = {
                "Accept": "application/hal+json",
            }
            if config.api_origin_oin:  # See Taiga #755
                headers["x-origin-oin"] = config.api_origin_oin
            if config.api_doelbinding:  # See Taiga #755
                headers["x-doelbinding"] = config.api_doelbinding

            data = client.retrieve(
                "ingeschrevenpersonen",
                url=url,
                request_kwargs=dict(
                    headers=headers,
                    params={
                        "fields": "geslachtsaanduiding,naam,geboorte,verblijfplaats"
                    },
                    verify=False,
                ),
            )
        except RequestException as e:
            logger.exception("exception while making request", exc_info=e)
            return {}
        except ClientError as e:
            logger.exception("exception while making request", exc_info=e)
            return {}

    return data


def update_brp_data_in_db(user, brp_version, initial=True):
    data = fetch_brp_data(user, brp_version)

    if brp_version == "2.0":
        if data.get("personen"):
            data = data.get("personen", [])[0]
        else:
            data = []

    if not data:
        logger.warning("no data retrieved from Haal Centraal")
    else:
        birthday = glom(data, "geboorte.datum.datum", default=None)
        if birthday:
            try:
                birthday = datetime.strptime(birthday, "%Y-%m-%d")
            except ValueError:
                birthday = None

        user.birthday = birthday
        user.first_name = glom(data, "naam.voornamen", default="")
        user.last_name = glom(data, "naam.geslachtsnaam", default="")
        user.street = glom(data, "verblijfplaats.straat", default="")
        user.housenumber = glom(data, "verblijfplaats.huisnummer", default="")
        user.city = glom(data, "verblijfplaats.woonplaats", default="")
        user.is_prepopulated = True

        if initial is False:
            user.save()

        system_action(_("data was retrieved from haal centraal"), content_object=user)
