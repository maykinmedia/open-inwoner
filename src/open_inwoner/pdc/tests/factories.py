from django.utils.text import slugify

import factory
import factory.fuzzy

from ..models import Category, Product


class ProductFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
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


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda a: slugify(a.name))
    description = factory.Faker("sentence")
    depth = 1

    class Meta:
        model = Category

    @factory.lazy_attribute
    def path(self):
        last_root = Category.get_last_root_node()
        if last_root:
            # Add the new root node as the last one
            newpath = last_root._inc_path()
        else:
            # Add the first root node
            newpath = Category._get_path(None, 1, 1)
        return newpath
