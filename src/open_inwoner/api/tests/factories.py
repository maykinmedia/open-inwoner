import factory

from ...accounts.models import Contact
from ...accounts.tests.factories import UserFactory


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    created_by = factory.SubFactory(UserFactory)
