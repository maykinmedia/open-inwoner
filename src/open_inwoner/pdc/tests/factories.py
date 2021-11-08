from django.utils.text import slugify

import factory
import factory.fuzzy

from ..models import Product


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda a: slugify(a.name))
    summary = factory.Faker("sentence")
    content = factory.Faker("paragraph")
