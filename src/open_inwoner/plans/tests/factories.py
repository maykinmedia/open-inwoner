from django.core.files.uploadedfile import SimpleUploadedFile

import factory

from open_inwoner.accounts.tests.factories import UserFactory


class FilerFileFactory(factory.django.DjangoModelFactory):
    file = factory.LazyAttribute(
        lambda _: SimpleUploadedFile(
            "example.txt",
            b"test",
        )
    )
    original_filename = "example.txt"
    name = "example.txt"

    class Meta:
        model = "filer.File"


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "plans.Plan"

    title = factory.Faker("first_name")
    goal = factory.Faker("last_name")
    end_date = factory.Faker("date")
    created_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def plan_contacts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.plan_contacts.add(user)


class PlanTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "plans.PlanTemplate"

    name = factory.Faker("word")
    file = factory.SubFactory(FilerFileFactory)
    goal = factory.Faker("paragraph")


class ActionTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "plans.ActionTemplate"

    plan_template = factory.SubFactory(PlanTemplateFactory)
    name = factory.Faker("word")
    description = factory.Faker("word")
    goal = factory.Faker("paragraph")
    end_in_days = factory.Faker("pyint")
