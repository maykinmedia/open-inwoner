import datetime

import factory

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.services import Question, QuestionValidator
from open_inwoner.utils.url import uuid_from_url


class ContactFormSubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "openklant.ContactFormSubject"

    subject = factory.Faker("sentence")
    subject_code = factory.Faker("word")


class KlantContactMomentAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "openklant.KlantContactMomentAnswer"

    contactmoment_url = factory.Faker("url")
    user = factory.SubFactory(UserFactory)


def make_question_from_contactmoment(
    contact_moment_data: dict,
    new_answer_available: bool = False,
) -> Question:
    return QuestionValidator.validate_python(
        {
            "identification": contact_moment_data["identificatie"],
            "api_source_url": contact_moment_data["url"],
            "api_source_uuid": uuid_from_url(contact_moment_data["url"]),
            "subject": contact_moment_data["onderwerp"],
            "question_text": contact_moment_data["tekst"],
            "answer_text": contact_moment_data["antwoord"],
            "registered_date": datetime.datetime.fromisoformat(
                contact_moment_data["registratiedatum"]
            ),
            "status": contact_moment_data["status"],
            "channel": contact_moment_data["kanaal"],
            "new_answer_available": new_answer_available,
            "api_service": KlantenServiceType.ESUITE,
        }
    )
