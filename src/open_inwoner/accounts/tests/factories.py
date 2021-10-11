import factory
import factory.fuzzy

from ..models import User


class UserFactory(factory.django.DjangoModelFactory):
    """
    Creates a default user with all relevant properties.
    """

    class Meta:
        model = User

    first_name = factory.fuzzy.FuzzyChoice(["John", "Jane"])
    last_name = "Doe"
    email = factory.LazyAttributeSequence(
        lambda a, n: "{0}.{1}-{2}@example.com".format(
            a.first_name.lower(), a.last_name.lower(), n
        )
    )
    password = factory.PostGenerationMethodCall("set_password", "secret")
