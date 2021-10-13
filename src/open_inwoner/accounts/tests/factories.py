import factory
import factory.fuzzy

from ..models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttributeSequence(
        lambda a, n: "{0}.{1}-{2}@example.com".format(
            a.first_name.lower(), a.last_name.lower(), n
        )
    )
    password = factory.PostGenerationMethodCall("set_password", "secret")
