import json
import os

from ..models import HaalCentraalConfig
from .factories import ServiceFactory


class HaalCentraalMixin:
    def _setUpService(self):
        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/brp",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

    def _setUpMocks_v_2(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_2.1.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=200,
            json=self.load_json_mock("ingeschrevenpersonen.999993847_2.1.json"),
        )

    def _setUpMocks_v_1_3(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_1.3.yaml"),
        )
        m.get(
            "https://personen/api/brp/ingeschrevenpersonen/999993847?fields=geslachtsaanduiding,naam,geboorte,verblijfplaats",
            status_code=200,
            json=self.load_json_mock("ingeschrevenpersonen.999993847_1.3.json"),
        )

    def load_json_mock(self, name):
        path = os.path.join(os.path.dirname(__file__), "files", name)
        with open(path, "r") as f:
            return json.load(f)

    def load_binary_mock(self, name):
        path = os.path.join(os.path.dirname(__file__), "files", name)
        with open(path, "rb") as f:
            return f.read()
