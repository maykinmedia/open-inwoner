import abc
from abc import ABC
from datetime import datetime

from django.core.exceptions import ImproperlyConfigured

import requests
import structlog
from glom import GlomError, glom
from zgw_consumers.client import build_client

from open_inwoner.haalcentraal.api_models import BRPData
from open_inwoner.haalcentraal.models import BrpVersionChoices, HaalCentraalConfig
from open_inwoner.utils.api import get_json_response

logger = structlog.stdlib.get_logger(__name__)


class BRPClient(ABC):
    version: str = NotImplemented

    def __init__(self, client, extra_headers: dict | None = None):
        self.client = client
        self.extra_headers = extra_headers or {}

    @classmethod
    def from_config(cls) -> "BRPClient":
        config = HaalCentraalConfig.get_solo()
        if not config.service:
            raise ImproperlyConfigured("No service configured for Haal Centraal")
        client = build_client(config.service)

        mapping = {
            BrpVersionChoices.V1_3: BRPClient_1_3,
            BrpVersionChoices.V2_0: BRPClient_2_0,
            BrpVersionChoices.V2_1: BRPClient_2_1,
        }
        klass = mapping.get(config.brp_version)
        if klass is None:
            raise NotImplementedError(
                f"no implementation for BRP version '{config.brp_version}'"
            )
        extra_headers = {
            item["key"]: item["value"] for item in config.headers if item.get("key")
        }
        return klass(client=client, extra_headers=extra_headers)

    @abc.abstractmethod
    def fetch_data(self, user_bsn: str) -> dict | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def parse_data(self, data: dict) -> BRPData | None:
        raise NotImplementedError()

    def fetch_brp(self, user_bsn: str) -> BRPData | None:
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


class BRPClient_1_3(BRPClient):
    version = "1.3"

    def fetch_data(self, user_bsn: str) -> dict | None:
        url = f"ingeschrevenpersonen/{user_bsn}"
        headers = {
            "Accept": "application/hal+json",
        }
        headers.update(self.extra_headers)

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

    def parse_data(self, data: dict) -> BRPData | None:
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


class _BRPClient_2_x(BRPClient):
    """Shared implementation base for BRP 2.x API versions."""

    def make_request(self, user_bsn: str) -> requests.Response:
        url = "personen"

        headers = {
            "Accept": "application/json",
        }
        headers.update(self.extra_headers)

        response = self.client.post(
            url=url,
            json={
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
            headers=headers,
            verify=False,
        )
        return response

    def fetch_data(self, user_bsn) -> dict | None:
        response = self.make_request(user_bsn)
        return get_json_response(response)

    def parse_data(self, data: dict) -> BRPData | None:
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


class BRPClient_2_0(_BRPClient_2_x):
    version = "2.0"


class BRPClient_2_1(_BRPClient_2_x):
    version = "2.1"
