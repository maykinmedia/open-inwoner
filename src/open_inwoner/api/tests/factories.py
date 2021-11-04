from uuid import uuid4

import factory
from rest_framework.authtoken.models import Token

from ...accounts.models import Contact
from ...accounts.tests.factories import UserFactory


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    created_by = factory.SubFactory(UserFactory)


class TokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token
        exclude = ("created_for",)

    created_for = factory.SubFactory(UserFactory)
    key = factory.LazyAttribute(lambda o: uuid4())
    user_id = factory.LazyAttribute(lambda o: o.created_for.id)
