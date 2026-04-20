import abc
from abc import ABC

from django.core.exceptions import ImproperlyConfigured

import requests
from zgw_consumers.client import build_client

from open_inwoner.haalcentraal.api_models import BRP2xPersoon, BRP13Persoon
from open_inwoner.haalcentraal.models import BrpVersionChoices, HaalCentraalConfig
from open_inwoner.utils.api import get_json_response


class BRPClient(ABC):
    def __init__(self, client, version: str, extra_headers: dict | None = None):
        self.client = client
        self.version = version
        self.extra_headers = extra_headers or {}

    @classmethod
    def from_config(cls) -> "BRPClient":
        config = HaalCentraalConfig.get_solo()
        if not config.service:
            raise ImproperlyConfigured("No service configured for Haal Centraal")
        client = build_client(config.service)
        extra_headers = {
            item["key"]: item["value"] for item in config.headers if item.get("key")
        }
        version = config.brp_version
        mapping = {
            BrpVersionChoices.V1_3: BRPClient13,
            BrpVersionChoices.V2_0: BRPClient2x,
            BrpVersionChoices.V2_1: BRPClient2x,
            BrpVersionChoices.V2_2: BRPClient2x,
            BrpVersionChoices.V2_3: BRPClient2x,
            BrpVersionChoices.V2_4: BRPClient2x,
            BrpVersionChoices.V2_5: BRPClient2x,
            BrpVersionChoices.V2_6: BRPClient2x,
            BrpVersionChoices.V2_7: BRPClient2x,
        }
        try:
            klass = mapping[version]
        except KeyError:
            raise NotImplementedError(
                f"no implementation for BRP version '{version}'"
            ) from None
        return klass(client=client, version=version, extra_headers=extra_headers)

    @abc.abstractmethod
    def fetch_brp_data_for_bsn(
        self, user_bsn: str
    ) -> BRP13Persoon | BRP2xPersoon | None:
        raise NotImplementedError()

    def __str__(self):
        return f"{self.__class__.__name__}({self.version})"


class BRPClient13(BRPClient):
    def fetch_brp_data_for_bsn(self, user_bsn: str) -> BRP13Persoon | None:
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
        )
        data = get_json_response(response, strict=True)
        if not data:
            return None
        return BRP13Persoon.model_validate(data)


class BRPClient2x(BRPClient):
    """Implementation for all BRP 2.x API versions (2.0–2.7).

    Changes between 2.1 and 2.7 are limited to gezag (custody) fields and
    search-by-address parameters, neither of which we request. The
    RaadpleegMetBurgerservicenummer operation with naam/geboorte/verblijfplaats
    fields is stable across all these versions.
    """

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
        )
        return response

    def fetch_brp_data_for_bsn(self, user_bsn: str) -> BRP2xPersoon | None:
        data = get_json_response(self.make_request(user_bsn), strict=True)
        personen = (data or {}).get("personen", [])
        if not personen:
            return None
        return BRP2xPersoon.model_validate(personen[0])
