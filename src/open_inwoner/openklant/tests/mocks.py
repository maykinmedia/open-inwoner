import uuid
from datetime import datetime

from django.urls import reverse


class MockKlantenService:
    def __init__(self, service_type: str):
        self.service_type = service_type
        self.identification = f"{service_type.value}_identification"
        self.subject = f"{service_type.value}_subject"
        self.url = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": service_type.value,
                "kcm_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            },
        )

    def list_questions(self, fetch_params={}, user=None):
        return [
            {
                "identification": self.identification,
                "url": self.url,
                "api_source_url": f"http://{self.service_type.value}.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "subject": self.subject,
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "new_answer_available": False,
                "api_service": self.service_type,
            }
        ]

    def retrieve_question(self, fetch_params={}, question_uuid="", user=None):
        return (
            {
                "identification": self.identification,
                "url": self.url,
                "api_source_url": f"http://{self.service_type.value}.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "subject": self.subject,
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "api_service": self.service_type,
                "new_answer_available": False,
            },
            None,
        )

    def list_questions_for_zaak(self, zaak=None, user=None):
        return [
            {
                "identification": self.identification,
                "url": self.url,
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "subject": self.subject,
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "api_service": self.service_type,
                "new_answer_available": False,
            }
        ]

    def get_fetch_parameters(self, request=None, user=None, use_vestigingsnummer=False):
        return {"user_bsn": "123456789"}
