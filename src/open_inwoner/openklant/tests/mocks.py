import uuid
from datetime import datetime

from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.services import OpenKlant2Question, QuestionsResult


class MockOpenKlant2Service:
    def __init__(self):
        self.service_type = KlantenServiceType.OPENKLANT2

    def get_fetch_parameters(self, user=None):
        return {"user_bsn": "123456789"}

    def get_or_create_partij_for_user(self, fetch_params=None, user=None):
        return {"uuid": "0d150ff9-0924-46f6-8ef9-17fee9e54d23"}, False

    def list_questions(self, fetch_params=None, user=None):
        return QuestionsResult(questions=[self.retrieve_question()[0]])

    def retrieve_question(
        self, fetch_params=None, question_uuid="", user=None, new_answer_available=False
    ):
        return (
            {
                "identification": "openklant2_identification",
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "api_source_uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"),
                "subject": "openklant2_subject",
                "question_text": "hello?",
                "answers": [
                    {
                        "text": "no",
                        "uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd"),
                        "registered_date": datetime.fromisoformat(
                            "2024-01-02T12:00:00Z"
                        ),
                    }
                ],
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

    def create_question_for_zaak(
        self,
        partij_uuid: str,
        question: str,
        zaak: str,
    ) -> OpenKlant2Question:
        return OpenKlant2Question(
            url="http://openklant/api/test/klantcontacten/9431676d-07ce-45e9-bfa8-db86c229b916",
            question_kcm_uuid="9431676d-07ce-45e9-bfa8-db86c229b916",
            question="What?",
            answers=[],
            onderwerp="Coffee zaak",
            kanaal="email",
            taal="nl",
            nummer="42",
            plaatsgevonden_op=datetime.fromisoformat("2024-01-01T12:00:00Z"),
        )
