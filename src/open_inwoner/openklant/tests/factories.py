import factory
from zgw_consumers.api_models.base import factory as zgw_factory

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.api_models import ContactMoment


class ContactFormSubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "openklant.ContactFormSubject"

    subject = factory.Faker("sentence")
    subject_code = factory.Faker("word")


def make_contactmoment(contact_moment_data: dict):
    return zgw_factory(ContactMoment, contact_moment_data)


class KlantContactMomentLocalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "openklant.KlantContactMomentLocal"

    contactmoment_url = factory.Faker("url")
    user = factory.SubFactory(UserFactory)
