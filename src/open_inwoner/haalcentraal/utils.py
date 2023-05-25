import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from django.conf import settings
from django.utils.translation import gettext as _

from glom import glom
from requests import RequestException
from zds_client import ClientError

from open_inwoner.haalcentraal.api_models import BRPData
from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.utils.logentry import system_action

logger = logging.getLogger(__name__)


def _fetch_brp_data(user_bsn: str, brp_version):
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
                    "burgerservicenummer": [user_bsn],
                },
                request_kwargs=dict(
                    headers={"Accept": "application/json"}, verify=False
                ),
            )
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return {}

    elif brp_version == "1.3":
        url = urljoin(client.base_url, f"ingeschrevenpersonen/{user_bsn}")
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
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return {}

    return data


def fetch_brp(user_bsn: str) -> Optional[BRPData]:
    if not user_bsn:
        return

    # TODO move BRP_VERSION to haalcentraal singleton
    brp_version = settings.BRP_VERSION
    data = _fetch_brp_data(user_bsn, brp_version)

    if brp_version == "2.0":
        if data.get("personen"):
            data = data.get("personen", [])[0]
        else:
            data = []

    if not data:
        logger.warning("no data retrieved from Haal Centraal")
        return

    birthday = glom(data, "geboorte.datum.datum", default=None)
    if birthday:
        try:
            birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
        except ValueError:
            birthday = None

    gender_glom = (
        "geslachtsaanduiding.omschrijving"
        if brp_version == "2.0"
        else "geslachtsaanduiding"
    )

    brp = BRPData(
        first_name=glom(data, "naam.voornamen", default=""),
        infix=glom(data, "naam.voorvoegsel", default=""),
        last_name=glom(data, "naam.geslachtsnaam", default=""),
        street=glom(data, "verblijfplaats.straat", default=""),
        housenumber=str(glom(data, "verblijfplaats.huisnummer", default="")),
        city=glom(data, "verblijfplaats.woonplaats", default=""),
        birthday=birthday,
        # extra fields
        initials=glom(data, "naam.voorletters", default=""),
        birthday_city=glom(data, "geboorte.plaats.omschrijving", default=""),
        gender=glom(data, gender_glom, default=""),
        postcode=glom(data, "verblijfplaats.postcode", default=""),
        country=glom(data, "verblijfplaats.land.omschrijving", default=""),
    )

    return brp


def update_brp_data_in_db(user, initial=True):
    data = fetch_brp(user.bsn)

    if not data:
        logger.warning("no data retrieved from Haal Centraal")
        return

    data.copy_to_user(user)
    user.is_prepopulated = True

    if initial is False:
        user.save()

    system_action(_("data was retrieved from haal centraal"), content_object=user)
