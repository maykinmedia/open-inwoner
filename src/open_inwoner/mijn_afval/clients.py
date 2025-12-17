import json
from pathlib import Path

from ape_pie.client import APIClient

from .api_models import BAGObject

DATA_PATH = (
    Path(__file__).resolve().parent / "tests" / "fixtures" / "afval-mock-data.json"
)


class AfvalApiClient(APIClient):
    def _load_data(self):
        return json.loads(DATA_PATH.read_text())

    def fetch_bag_objects_for_bsn(self, bsn: str) -> list[BAGObject]:
        """
        Fetch 'Basisregistratie Adressen en Gebouwen' objects for specific BSN
        """
        data = self._load_data()

        if not data:
            return []

        return [BAGObject.model_validate(obj) for obj in data]
