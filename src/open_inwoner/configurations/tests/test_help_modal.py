from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import ProductFactory

from ..models import SiteConfiguration
from .factories import SiteConfigurationFactory


class TestHelpContext(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()

    def test_default_help_text_on_home_page(self):
        response = self.app.get(reverse("root"))
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(
            help_text,
            _(
                "Welkom! Op dit scherm vindt u een overzicht van de verschillende thema's en producten & diensten."
            ),
        )

    def test_custom_help_text_on_home_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("root"))
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(help_text, config.home_help_text)

    def test_default_help_text_on_themes_page(self):
        response = self.app.get(reverse("pdc:category_list"))
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(
            help_text,
            _(
                "Op dit scherm vindt u de verschillende thema's waarvoor wij producten en diensten aanbieden."
            ),
        )

    def test_custom_help_text_on_themes_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("pdc:category_list"))
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(help_text, config.theme_help_text)

    def test_default_help_text_on_products_page(self):
        response = self.app.get(
            reverse("pdc:product_detail", kwargs={"slug": self.product.slug})
        )
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(
            help_text,
            _(
                "Op dit scherm kunt u de details vinden over het gekozen product of dienst. Afhankelijk van het product kunt u deze direct aanvragen of meer informatie opvragen."
            ),
        )

    def test_custom_help_text_on_products_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(
            reverse("pdc:product_detail", kwargs={"slug": self.product.slug})
        )
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(help_text, config.product_help_text)

    def test_default_help_text_on_search_page(self):
        response = self.app.get(reverse("search:search"))
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(
            help_text,
            _("Op dit scherm kunt u zoeken naar de producten en diensten."),
        )

    def test_custom_help_text_on_search_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("search:search"))
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(help_text, config.search_help_text)

    def test_default_help_text_on_profile_page(self):
        response = self.app.get(reverse("accounts:my_profile"), user=self.user)
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(
            help_text,
            _(
                "Op dit scherm ziet u uw persoonlijke profielgegevens en gerelateerde gegevens."
            ),
        )

    def test_custom_help_text_on_profile_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("accounts:my_profile"), user=self.user)
        help_text = response.context.get("configurable_text", {}).get("help")

        self.assertEquals(help_text, config.account_help_text)
