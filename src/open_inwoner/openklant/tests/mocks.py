import uuid
from datetime import datetime

from ..constants import KlantenServiceType


class MockOpenKlant2Service:
    def __init__(self):
        self.service_type = KlantenServiceType.OPENKLANT2

    def list_questions(self, fetch_params={}, user=None):
        return [self.retrieve_question()[0]]

    def retrieve_question(
        self, fetch_params={}, question_uuid="", user=None, new_answer_available=False
    ):
        return (
            {
                "identification": "openklant2_identification",
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "api_source_uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"),
                "subject": "openklant2_subject",
                "question_text": "hello?",
                "answer_text": "no",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "status": "Onbekend",
                "channel": "email",
                "new_answer_available": new_answer_available,
                "api_service": self.service_type,
            },
            None,
        )

    def list_questions_for_zaak(self, zaak=None, user=None):
        return [self.retrieve_question()[0]]

    def get_fetch_parameters(self, request=None, user=None, use_vestigingsnummer=False):
        return {"user_bsn": "123456789"}
