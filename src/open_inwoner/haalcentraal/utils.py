import logging
from urllib.parse import urljoin

from django.utils.translation import gettext as _

from requests import RequestException
from zds_client import ClientError

from open_inwoner.haalcentraal.models import HaalCentraalConfig

logger = logging.getLogger(__name__)


def fetch_brb_data(instance, brp_version):
    config = HaalCentraalConfig.get_solo()

    if not config.service:
        logger.warning("no service defined for Haal Centraal")
        return {}

    client = config.service.build_client()
    logger.warning(brp_version)
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
                    headers={"Accept": "application/hal+json"}, verify=False
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
            data = client.retrieve(
                "ingeschrevenpersonen",
                url=url,
                request_kwargs=dict(
                    headers={
                        "Accept": "application/hal+json",
                        "x-doelbinding": "Huisvesting",  # See Taiga #755
                        "x-origin-oin": "00000003273229750000",
                    },  # See Taiga #755
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
