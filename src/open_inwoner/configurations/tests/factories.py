import factory

from ..models import SiteConfiguration


class SiteConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteConfiguration

    name = factory.Faker("name")
    home_help_text = factory.Faker("paragraph", nb_sentences=2)
    theme_help_text = factory.Faker("paragraph", nb_sentences=2)
    product_help_text = factory.Faker("paragraph", nb_sentences=2)
    search_help_text = factory.Faker("paragraph", nb_sentences=2)
    account_help_text = factory.Faker("paragraph", nb_sentences=2)
