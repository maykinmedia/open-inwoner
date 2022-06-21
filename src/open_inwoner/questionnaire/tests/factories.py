from django.utils.text import slugify

import factory

from ..models import QuestionnaireStep, QuestionnaireStepFile


class QuestionnaireStepFactory(factory.django.DjangoModelFactory):
    depth = 1
    path = "0001"
    question = factory.Faker("sentence")
    code = factory.LazyAttribute(lambda a: slugify(a.question))
    slug = factory.LazyAttribute(lambda a: slugify(a.question))
    help_text = factory.Faker("sentence")

    class Meta:
        model = QuestionnaireStep


class QuestionnaireStepFileFactory(factory.django.DjangoModelFactory):
    questionnaire_step = factory.SubFactory(QuestionnaireStepFactory)

    class Meta:
        model = QuestionnaireStepFile
