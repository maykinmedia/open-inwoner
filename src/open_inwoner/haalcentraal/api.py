import abc
import logging
from abc import ABC
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from glom import GlomError, glom
from requests import RequestException
from zgw_consumers.client import build_client

from open_inwoner.haalcentraal.api_models import BRPData
from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.utils.api import ClientError, get_json_response

logger = logging.getLogger(__name__)


class BRPAPI(ABC):
    version: str = NotImplemented
    _is_ready = False

    def __init__(self):
        self.config = HaalCentraalConfig.get_solo()
        if not self.config.service:
            logger.warning("no service defined for Haal Centraal")
        else:
            self.client = build_client(self.config.service)
            self._is_ready = True

    @abc.abstractmethod
    def fetch_data(self, user_bsn: str) -> Optional[dict]:
        raise NotImplementedError()

    @abc.abstractmethod
    def parse_data(self, data: dict) -> Optional[BRPData]:
        raise NotImplementedError()

    def fetch_brp(self, user_bsn: str) -> Optional[BRPData]:
        if not self._is_ready:
            return None

        data = self.fetch_data(user_bsn)
        if not data:
            logger.warning("no data retrieved from Haal Centraal")
            return None
        obj = self.parse_data(data)
        return obj

    def glom_date(self, data, path, default=None):
        try:
            value = glom(data, path)
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (GlomError, ValueError):
            return default

    def __str__(self):
        return f"{self.__class__.__name__}({self.version})"


class BRP_1_3(BRPAPI):
    version = "1.3"

    def fetch_data(self, user_bsn: str) -> Optional[dict]:
        url = urljoin(self.client.base_url, f"ingeschrevenpersonen/{user_bsn}")
        headers = {
            "Accept": "application/hal+json",
        }
        if self.config.api_origin_oin:  # See Taiga #755
            headers["x-origin-oin"] = self.config.api_origin_oin
        if self.config.api_doelbinding:  # See Taiga #755
            headers["x-doelbinding"] = self.config.api_doelbinding

        try:
            response = self.client.get(
                url=url,
                headers=headers,
                params={
                    "fields": "geslachtsaanduiding,"
                    "naam.voornamen,naam.geslachtsnaam,naam.voorletters,naam.voorvoegsel,"
                    "verblijfplaats.straat,verblijfplaats.huisletter,"
                    "verblijfplaats.huisnummertoevoeging,verblijfplaats.woonplaats,"
                    "verblijfplaats.postcode,verblijfplaats.land.omschrijving,"
                    "geboorte.datum.datum,geboorte.plaats.omschrijving"
                },
                verify=False,
            )
            return get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return None

    def parse_data(self, data: dict) -> Optional[BRPData]:
        brp = BRPData(
            first_name=glom(data, "naam.voornamen", default=""),
            infix=glom(data, "naam.voorvoegsel", default=""),
            initials=glom(data, "naam.voorletters", default=""),
            last_name=glom(data, "naam.geslachtsnaam", default=""),
            street=glom(data, "verblijfplaats.straat", default=""),
            housenumber=str(glom(data, "verblijfplaats.huisnummer", default="")),
            houseletter=glom(data, "verblijfplaats.huisletter", default=""),
            housenumbersuffix=glom(
                data, "verblijfplaats.huisnummertoevoeging", default=""
            ),
            city=glom(data, "verblijfplaats.woonplaats", default=""),
            postal_code=glom(data, "verblijfplaats.postcode", default=""),
            country=glom(data, "verblijfplaats.land.omschrijving", default=""),
            birthday=self.glom_date(data, "geboorte.datum.datum", default=None),
            # extra fields
            birth_place=glom(data, "geboorte.plaats.omschrijving", default=""),
            gender=glom(data, "geslachtsaanduiding", default=""),
        )
        return brp


class BRP_2_1(BRPAPI):
    version = "2.1"

    def fetch_data(self, user_bsn: str) -> Optional[dict]:
        url = urljoin(self.client.base_url, "personen")
        try:
            response = self.client.post(
                url=url,
                data={
                    "fields": [
                        "naam.geslachtsnaam",
                        "naam.voorletters",
                        "naam.voornamen",
                        "naam.voorvoegsel",
                        "geslacht.omschrijving",
                        "geboorte.plaats.omschrijving",
                        "geboorte.datum.datum",
                        "verblijfplaats.verblijfadres.officieleStraatnaam",
                        "verblijfplaats.verblijfadres.huisnummer",
                        "verblijfplaats.verblijfadres.huisletter",
                        "verblijfplaats.verblijfadres.huisnummertoevoeging",
                        "verblijfplaats.verblijfadres.postcode",
                        "verblijfplaats.verblijfadres.woonplaats",
                    ],
                    "type": "RaadpleegMetBurgerservicenummer",
                    "burgerservicenummer": [user_bsn],
                },
                headers={"Accept": "application/json"},
                verify=False,
            )
            return get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return None

    def parse_data(self, data: dict) -> Optional[BRPData]:
        # use first record
        if not data["personen"]:
            return None
        data = data["personen"][0]

        brp = BRPData(
            first_name=glom(data, "naam.voornamen", default=""),
            infix=glom(data, "naam.voorvoegsel", default=""),
            last_name=glom(data, "naam.geslachtsnaam", default=""),
            initials=glom(data, "naam.voorletters", default=""),
            street=glom(
                data, "verblijfplaats.verblijfadres.officieleStraatnaam", default=""
            ),
            housenumber=str(
                glom(data, "verblijfplaats.verblijfadres.huisnummer", default="")
            ),
            houseletter=glom(
                data, "verblijfplaats.verblijfadres.huisletter", default=""
            ),
            housenumbersuffix=glom(
                data, "verblijfplaats.verblijfadres.huisnummertoevoeging", default=""
            ),
            city=glom(data, "verblijfplaats.verblijfadres.woonplaats", default=""),
            postal_code=glom(data, "verblijfplaats.verblijfadres.postcode", default=""),
            birthday=self.glom_date(data, "geboorte.datum.datum", default=None),
            birth_place=glom(data, "geboorte.plaats.omschrijving", default=""),
            gender=glom(data, "geslacht.omschrijving", default=""),
            # we don't have country in 2.x (address defaults to Nederland)
            # country=glom(data, "verblijfplaats.land.omschrijving", default=""),
        )
        return brp
