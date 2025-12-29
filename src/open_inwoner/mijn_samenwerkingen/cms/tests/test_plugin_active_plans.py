from django.test import override_settings

from django_webtest import WebTest

from open_inwoner.core.cms.utils import cms_test_utils as cms_tools
from open_inwoner.onderwerpen.cms.cms_apps import ProductsApphook
from open_inwoner.onderwerpen.cms.cms_plugins import ProductFinderPlugin
from open_inwoner.onderwerpen.forms import ProductFinderForm
from open_inwoner.onderwerpen.tests.factories import ProductConditionFactory


@override_settings(ROOT_URLCONF="open_inwoner.core.cms.tests.urls")
class TestProductFinder(WebTest):
    def test_product_location_link_is_rendered_in_plugin(self):
        cms_tools.create_apphook_page(ProductsApphook)

        condition = ProductConditionFactory(question="Question 1")

        html, context = cms_tools.render_plugin(ProductFinderPlugin)

        self.assertEqual(context["condition"], condition)
        self.assertIsInstance(context["condition_form"], ProductFinderForm)

    def test_no_output_generated_without_apphook(self):
        html, context = cms_tools.render_plugin(ProductFinderPlugin)
        self.assertEqual("", html)
