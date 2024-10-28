import datetime
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

    def update_object(self, uuid: str, updated_data: dict):

        # TODO: the PATCH method in the Objects API does not appear to work as
        # expected. It validates the partial against the JSON Schema, so in this
        # case you have to supply an object that is valid according to the
        # schema. We thus have to do our own merging.

        # Also: we are usign the underlying API directly to avoid going back and
        # forth between camel and snake case.
        existing_obj = self.client.objects_api.retrieve("object", uuid=uuid)
        existing_data = existing_obj["record"]["data"]
        self.client.objects_api.partial_update(
            "object",
            {
                "record": {
                    "startAt": datetime.date.today().isoformat(),
                    "data": existing_data | updated_data,
                }
            },
            uuid=uuid,
        )
        # Refresh the object and build the Bericht model
        return self.client.get_object(uuid)
