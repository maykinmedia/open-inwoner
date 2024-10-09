import factory.fuzzy

from open_inwoner.pdc.tests.factories import ProductFactory as ProductTypeFactory

from ..models import Price, PriceOption


class PriceFactory(factory.django.DjangoModelFactory):
    valid_from = factory.Faker("date")
    product_type = factory.SubFactory(ProductTypeFactory)

    class Meta:
        model = Price


class PriceOptionFactory(factory.django.DjangoModelFactory):
    description = factory.Faker("sentence")
    amount = factory.fuzzy.FuzzyDecimal(1, 10)
    price = factory.SubFactory(PriceFactory)

    class Meta:
        model = PriceOption
