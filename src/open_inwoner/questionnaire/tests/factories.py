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

    @factory.post_generation
    def related_products(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for related_product in extracted:
                self.related_products.add(related_product)


class QuestionnaireStepFileFactory(factory.django.DjangoModelFactory):
    questionnaire_step = factory.SubFactory(QuestionnaireStepFactory)

    class Meta:
        model = QuestionnaireStepFile
