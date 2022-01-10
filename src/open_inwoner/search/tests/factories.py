import factory

from open_inwoner.accounts.tests.factories import UserFactory

from ..models import Feedback, Synonym


class SynonymFactory(factory.django.DjangoModelFactory):
    term = factory.Faker("word")
    synonyms = factory.List([factory.Faker("word") for _ in range(5)])

    class Meta:
        model = Synonym


class FeedbackFactory(factory.django.DjangoModelFactory):
    search_query = factory.Faker("sentence", nb_words=3)
    search_url = factory.Faker("uri")
    positive = factory.Faker("boolean")
    remark = factory.Faker("sentence")
    searched_by = factory.SubFactory(UserFactory)

    class Meta:
        model = Feedback
