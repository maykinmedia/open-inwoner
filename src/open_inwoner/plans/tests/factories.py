import factory

from open_inwoner.accounts.tests.factories import UserFactory


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "plans.Plan"

    title = factory.Faker("first_name")
    goal = factory.Faker("last_name")
    end_date = factory.Faker("date")
    created_by = factory.SubFactory(UserFactory)
