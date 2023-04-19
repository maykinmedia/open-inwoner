from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import ProductFactory

from ..models import SiteConfiguration
from .factories import SiteConfigurationFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestHelpContext(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()

    def test_default_help_text_on_home_page(self):
        response = self.app.get(reverse("root"))
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _(
                "Welkom! Op dit scherm vindt u een overzicht van de verschillende onderwerpen en producten & diensten."
            ),
        )

    def test_custom_help_text_on_home_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("root"))
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.home_help_text)

    def test_default_help_text_on_categories_page(self):
        response = self.app.get(reverse("products:category_list"))
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _(
                "Op dit scherm vindt u de verschillende onderwerpen waarvoor wij producten en diensten aanbieden."
            ),
        )

    def test_custom_help_text_on_categories_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("products:category_list"))
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.theme_help_text)

    def test_default_help_text_on_products_page(self):
        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": self.product.slug})
        )
        help_text = response.context.get("help_text")

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
            reverse("products:product_detail", kwargs={"slug": self.product.slug})
        )
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.product_help_text)

    def test_default_help_text_on_search_page(self):
        response = self.app.get(reverse("search:search"))
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _("Op dit scherm kunt u zoeken naar de producten en diensten."),
        )

    def test_custom_help_text_on_search_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("search:search"))
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.search_help_text)

    def test_default_help_text_on_profile_page(self):
        response = self.app.get(reverse("profile:detail"), user=self.user)
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _(
                "Op dit scherm ziet u uw persoonlijke profielgegevens en gerelateerde gegevens."
            ),
        )

    def test_custom_help_text_on_profile_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("profile:detail"), user=self.user)
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.account_help_text)

    def test_default_help_text_on_questionnaire_page(self):
        response = self.app.get(reverse("questionnaire_set:questionnaire_list"))
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _(
                "Het onderdeel Zelfdiagnose stelt u in staat om met het beantwoorden van enkele vragen een advies te krijgen van de gemeente, met concrete vervolgstappen en producten en diensten. U kunt tevens uw antwoorden en het advies bewaren om met een begeleider van de gemeente te bespreken."
            ),
        )

    def test_custom_help_text_on_questionnaire_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("questionnaire_set:questionnaire_list"))
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.questionnaire_help_text)

    def test_default_help_text_on_plan_page(self):
        response = self.app.get(reverse("collaborate:plan_list"), user=self.user)
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _(
                "Met het onderdeel Samenwerken kunt u samen met uw contactpersonen of begeleider van de gemeente aan de slag om met een samenwerkingsplan uw persoonlijke situatie te verbeteren. Door samen aan uw doelen te werken en acties te omschrijven kunnen we elkaar helpen."
            ),
        )

    def test_custom_help_text_on_plan_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("collaborate:plan_list"), user=self.user)
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.plan_help_text)
