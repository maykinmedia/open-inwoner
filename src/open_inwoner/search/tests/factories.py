import factory

from ..models import Synonym


class SynonymFactory(factory.django.DjangoModelFactory):
    term = factory.Faker("word")
    synonyms = factory.List([factory.Faker("word") for _ in range(5)])

    class Meta:
        model = Synonym
