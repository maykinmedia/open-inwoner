from .factories import ObjectsAPIConfigFactory


class TaakMockData:
    def __init__(self):
        self.mock_task_url_1 = {
            "url": "http://example0.com/api/v2/objects/f58d9f41-78de-4d59-89ef-c439c5c24510",
            "uuid": "f58d9f41-78de-4d59-89ef-c439c5c24510",
            "type": "http://example1.com/api/v2/objecttypes/2a3030c1-b4eb-4ca5-a3b4-13dd21954002",
            "record": {
                "index": 1,
                "typeVersion": 1,
                "data": {
                    "soort": "url",
                    "titel": "Test taak",
                    "status": "open",
                    "eigenaar": "OIP",
                    "identificatie": {"type": "bsn", "value": "123456789"},
                    "verloopdatum": "2025-09-20T18:25:43.524Z",
                    "koppeling": None,
                    "url": {"uri": "http://example.com"},
                    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
                },
                "geometry": None,
                "startAt": "2025-03-10",
                "endAt": "2030-03-10",
                "registrationAt": "2025-03-10",
                "correctionFor": 1,
                "correctedBy": 2,
            },
        }
        self.mock_task_url_2 = {
            "url": "http://example0.com/api/v2/objects/3da7c3e6-e8fd-4b77-80f3-c70ee5c2742d",
            "uuid": "3da7c3e6-e8fd-4b77-80f3-c70ee5c2742d",
            "type": "http://example1.com/api/v2/objecttypes/5ed4afd2-068e-49a8-a825-adb7117a1213",
            "record": {
                "index": 1,
                "typeVersion": 1,
                "data": {
                    "soort": "url",
                    "titel": "Test taak",
                    "status": "open",
                    "eigenaar": "OIP",
                    "identificatie": {"type": "bsn", "value": "987654321"},
                    "verloopdatum": "2026-09-20T18:25:43.524Z",
                    "koppeling": None,
                    "url": {"uri": "http://example2.com"},
                    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
                },
                "geometry": None,
                "startAt": "2025-03-10",
                "endAt": "2030-03-10",
                "registrationAt": "2025-03-10",
                "correctionFor": 1,
                "correctedBy": 2,
            },
        }
        self.mock_task_portaalformulier = {
            "url": "http://example0.com/api/v2/objects/f93e281a-2e92-4fd0-83cc-e4620de6f5a9",
            "uuid": "f93e281a-2e92-4fd0-83cc-e4620de6f5a9",
            "type": "http://example1.com/api/v2/objecttypes/027c3386-87db-441c-968b-ddcc702e1e61",
            "record": {
                "index": 1,
                "typeVersion": 1,
                "data": {
                    "soort": "portaalformulier",
                    "titel": "Test taak",
                    "status": "open",
                    "eigenaar": "OIP",
                    "identificatie": {"type": "bsn", "value": "987654321"},
                    "verloopdatum": "2026-09-20T18:25:43.524Z",
                    "koppeling": None,
                    "url": {"uri": "http://example2.com"},
                    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
                },
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
        ObjectsAPIConfigFactory(
            objects_api_service__label="API-objects",
            objects_api_service__api_root="http://www.objects-api.nl/api/v1",
            objects_api_service__slug="api-objects",
        )

    def install_mocks(self, m) -> "TaakMockData":
        m.get(
            "http://www.objects-api.nl/api/v1/objects",
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    self.mock_task_url_1,
                    self.mock_task_url_2,
                    self.mock_task_portaalformulier,
                ],
            },
        )
        m.get(
            "http://www.objects-api.nl/api/v1/objecttypes",
            json={
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            },
        )

        return self
