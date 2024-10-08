from typing import Literal

from objectsapiclient.client import Client as ObjectenClient
from objectsapiclient.models import Configuration

from open_inwoner.berichten.api_models import Bericht


class BerichtenService:

    client: ObjectenClient

    def __init__(self, client: ObjectenClient | None = None):
        self.client = client or Configuration.get_solo().client

    def fetch_berichten_for_bsn(self, bsn: str):
        return self.fetch_berichten_for_identificatie("bsn", bsn)

    def fetch_berichten_for_kvk(self, kvk: str):
        return self.fetch_berichten_for_identificatie("kvk", kvk)

    def fetch_berichten_for_identificatie(
        self, identificatie_type: Literal["bsn", "kvk"], identificatie_value: str
    ):
        objects = self.client.get_objects(
            object_type_uuid="98b9b5dd-9c2c-44ba-b5bf-13edaed668f9",
            data_attrs=[
                f"identificatie__type__exact__{identificatie_type}",
                f"identificatie__value__exact__{identificatie_value}",
            ],
        )

        return [
            Bericht.model_validate(obj.record["data"] | {"object_uuid": obj.uuid})
            for obj in objects
        ]

    def fetch_bericht(self, uuid: str):
        obj = self.client.get_object(uuid)

        return Bericht.model_validate(obj.record["data"] | {"object_uuid": obj.uuid})
