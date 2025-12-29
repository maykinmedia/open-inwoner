from urllib.parse import quote

from .factories import ObjectsAPIServiceConfigFactory

OBJECTS_API_ROOT = "http://www.objects-api.nl/api/v1"
OBJECT_TYPE_API_ROOT = "http://www.object-type-api.nl/api/v1"

UUID_OBJECT_TYPE_DIMPACT = "2a3030c1-b4eb-4ca5-a3b4-13dd21954002"
UUID_OBJECT_TYPE_DIENSVERLENING_1 = "e45ae321-77ef-483b-bcf9-329dacf88ff3"
UUID_OBJECT_TYPE_DIENSVERLENING_2 = "5ed4afd2-068e-49a8-a825-adb7117a1213"


class TaakMockData:
    def __init__(self):
        self.mock_task_data_externformulier_1 = {
            "soort": "externformulier",
            "titel": "Externe Taak 1",
            "status": "open",
            "eigenaar": "OIP",
            "betrokkene": {
                "source": "digid",
                "authorizee": {
                    "legalSubject": {
                        "identifier": "123456789",
                        "identifierType": "digid",
                    }
                },
                "levelOfAssurance": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
            },
            "toelichting": "Aanvraag Voorbeeld",
            "doorlooptijd": "P14D",
            "verloopdatum": "2025-09-15T23:59:59Z",
            "portaalformulier": {
                "data": {"volledige_naam": "Jan de Vries"},
                "formulier": {
                    "soort": "url",
                    "value": "http://portaalformulier-url/formulier/startpagina",
                },
                "verzonden_data": {},
            },
            "verwerker_taak_id": "0d59ada7-eacb-4129-8b7e-9907cd82c6d0",
        }
        self.mock_task_data_externformulier_2 = {
            "soort": "externformulier",
            "titel": "Externe Taak 2",
            "status": "open",
            "eigenaar": "OIP",
            "betrokkene": {
                "source": "digid",
                "authorizee": {
                    "legalSubject": {
                        "identifier": "987654321",
                        "identifierType": "digid",
                    }
                },
                "levelOfAssurance": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
            },
            "toelichting": "Aanvraag Voorbeeld",
            "doorlooptijd": "P14D",
            "verloopdatum": "2025-12-15T23:59:59Z",
            "portaalformulier": {
                "data": {"volledige_naam": "Thomas de Vries"},
                "formulier": {
                    "soort": "url",
                    "value": "http://portaalformulier-url/formulier-2/startpagina",
                },
                "verzonden_data": {},
            },
            "verwerker_taak_id": "0d59ada7-eacb-4129-8b7e-9907cd82c6d0",
        }
        self.mock_task_data_url = {
            "soort": "url",
            "titel": "Url taak",
            "status": "open",
            "eigenaar": "OIP",
            "identificatie": {
                "type": "bsn",
                "value": "123456789",
            },
            "verloopdatum": "2025-09-20T18:25:43.524Z",
            "koppeling": None,
            "task_url": {"uri": "http://www.url-task-example.nl"},
            "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
        }

        self.mock_task_externformulier_1 = {
            "url": f"{OBJECTS_API_ROOT}/objects/f58d9f41-78de-4d59-89ef-c439c5c24510",
            "uuid": "f58d9f41-78de-4d59-89ef-c439c5c24510",
            "type": f"{OBJECT_TYPE_API_ROOT}/objecttypes/{UUID_OBJECT_TYPE_DIENSVERLENING_1}/",
            "record": {
                "index": 1,
                "typeVersion": 1,
                "data": self.mock_task_data_externformulier_1,
                "geometry": None,
                "startAt": "2025-03-10",
                "endAt": "2030-03-10",
                "registrationAt": "2025-03-10",
                "correctionFor": 1,
                "correctedBy": 2,
            },
        }
        self.mock_task_externformulier_2 = {
            "url": f"{OBJECTS_API_ROOT}/objects/3da7c3e6-e8fd-4b77-80f3-c70ee5c2742d",
            "uuid": "3da7c3e6-e8fd-4b77-80f3-c70ee5c2742d",
            "type": f"{OBJECT_TYPE_API_ROOT}/objecttypes/{UUID_OBJECT_TYPE_DIENSVERLENING_2}/",
            "record": {
                "index": 1,
                "typeVersion": 1,
                "data": self.mock_task_data_externformulier_2,
                "geometry": None,
                "startAt": "2025-03-10",
                "endAt": "2030-03-10",
                "registrationAt": "2025-03-10",
                "correctionFor": 1,
                "correctedBy": 2,
            },
        }
        self.mock_task_url = {
            "url": f"{OBJECTS_API_ROOT}/objects/4db3491d-6ae1-4674-ba82-622f963b51d8",
            "uuid": "4db3491d-6ae1-4674-ba82-622f963b51d8",
            "type": f"{OBJECT_TYPE_API_ROOT}/objecttypes/{UUID_OBJECT_TYPE_DIMPACT}/",
            "record": {
                "index": 1,
                "typeVersion": 1,
                "data": self.mock_task_data_url,
                "geometry": None,
                "startAt": "2025-03-10",
                "endAt": "2030-03-10",
                "registrationAt": "2025-03-10",
                "correctionFor": 1,
                "correctedBy": 2,
            },
        }

    @classmethod
    def setUpServices(cls):
        ObjectsAPIServiceConfigFactory(
            objecttypes_api_client_config__api_root=OBJECT_TYPE_API_ROOT,
            objects_api_client_config__label="API-objects",
            objects_api_client_config__api_root=OBJECTS_API_ROOT,
            objects_api_client_config__slug="api-objects",
        )

    def install_mocks(self, m) -> "TaakMockData":
        # Encode object type base URL for query parameter
        encoded_object_type_base = quote(
            f"{OBJECT_TYPE_API_ROOT}/objecttypes/", safe=""
        )

        # UUID_OBJECT_TYPE_DIMPACT
        m.get(
            f"{OBJECTS_API_ROOT}/objects?type={encoded_object_type_base}{UUID_OBJECT_TYPE_DIMPACT}%2F",
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    self.mock_task_url,
                ],
            },
        )

        # UUID_OBJECT_TYPE_DIENSVERLENING_1
        m.get(
            f"{OBJECTS_API_ROOT}/objects?type={encoded_object_type_base}{UUID_OBJECT_TYPE_DIENSVERLENING_1}%2F",
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    self.mock_task_externformulier_1,
                ],
            },
        )
        # UUID_OBJECT_TYPE_DIENSVERLENING_2
        m.get(
            f"{OBJECTS_API_ROOT}/objects?type={encoded_object_type_base}{UUID_OBJECT_TYPE_DIENSVERLENING_2}%2F",
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    self.mock_task_externformulier_2,
                ],
            },
        )

        m.get(
            f"{OBJECTS_API_ROOT}objecttypes",
            json={
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            },
        )

        return self
