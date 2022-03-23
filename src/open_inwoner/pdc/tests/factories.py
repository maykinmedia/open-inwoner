from django.contrib.gis.geos import Point
from django.utils.text import slugify

import factory.fuzzy

from ..models import (
    Category,
    Organization,
    OrganizationType,
    Product,
    ProductCondition,
    ProductContact,
    ProductLocation,
    Tag,
)


class ProductFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"product {n}")
    slug = factory.LazyAttribute(lambda a: slugify(a.name))
    summary = factory.Faker("sentence")
    content = factory.Faker("paragraph")

    class Meta:
        model = Product

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for category in extracted:
                self.categories.add(category)

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for location in extracted:
                self.locations.add(location)


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda a: slugify(a.name))
    description = factory.Faker("sentence")

    class Meta:
        model = Category

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """For now factory creates only root categories"""
        return Category.add_root(**kwargs)


class TagFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda a: slugify(a.name))

    class Meta:
        model = Tag


class OrganizationTypeFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = OrganizationType


class OrganizationFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda a: slugify(a.name))
    type = factory.SubFactory(OrganizationTypeFactory)
    street = factory.Faker("street_name", locale="nl_NL")
    postcode = factory.Faker("postcode", locale="nl_NL")
    geometry = Point(5, 52)

    class Meta:
        model = Organization


class ProductContactFactory(factory.django.DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    phonenumber = factory.Faker("phone_number")

    class Meta:
        model = ProductContact


class ProductLocationFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    street = factory.Faker("street_name", locale="nl_NL")
    postcode = factory.Faker("postcode", locale="nl_NL")
    geometry = Point(5, 52)

    class Meta:
        model = ProductLocation


class ProductConditionFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    question = factory.Faker("word")
    positive_text = factory.Faker("word")
    negative_text = factory.Faker("word")
    rule = factory.Faker("word")

    class Meta:
        model = ProductCondition
