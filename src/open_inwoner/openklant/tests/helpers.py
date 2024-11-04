from django.test import TestCase as DjangoTestCase

from typing_extensions import TypedDict
from vcr.record_mode import RecordMode
from vcr.unittest import VCRMixin

from open_inwoner.conf.utils import config
from openklant2.tests.helpers import LiveOpenKlantTestMixin


class OpenKlant2ServiceTestConfig(TypedDict):
    use_live_service: bool
    vcr_record_mode: RecordMode


class Openklant2ServiceTestCase(VCRMixin, LiveOpenKlantTestMixin, DjangoTestCase):
    vcr_record_mode: RecordMode = RecordMode.NONE

    @classmethod
    def get_config(cls) -> OpenKlant2ServiceTestConfig:
        record_openklant_cassettes = config("RECORD_OPENKLANT_CASSETTES", default=False)
        return {
            "use_live_service": record_openklant_cassettes,
            "vcr_record_mode": (
                RecordMode.ALL if record_openklant_cassettes else cls.vcr_record_mode
            ),
        }

    @classmethod
    def should_bypass_live_server(cls) -> bool:
        return cls.get_config()["use_live_service"] is False

    def _get_vcr(self, **kwargs):
        vcr = super()._get_vcr(**kwargs)
        vcr.record_mode = self.get_config()["vcr_record_mode"]
        vcr.match_on = [
            "method",
            "scheme",
            "host",
            "port",
            "path",
            "query",
        ]
        return vcr

    @property
    def openklant2_api_root(self):
        return self._service._api_root

    @property
    def openklant2_api_path(self):
        return self._service._api_path

    @property
    def openklant2_api_token(self):
        return self._service._api_token
