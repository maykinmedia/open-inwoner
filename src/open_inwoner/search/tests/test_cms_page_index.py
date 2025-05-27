from django.contrib.sites.models import Site
from django.test import TestCase

from cms.api import add_plugin
from cms.models import Page
from cms.plugin_rendering import ContentRenderer
from cms.utils.page import get_page_queryset
from cms.utils.plugins import get_plugins

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.banner.cms_plugins import BannerTextPlugin
from open_inwoner.cms.tests import cms_tools


class PlaceholderRenderer:
    """Simple utility to render placeholder content directly"""

    @staticmethod
    def render_placeholder(placeholder, language="nl"):
        """Render a placeholder's content without using the test client"""
        renderer = ContentRenderer(request=None)
        plugins = get_plugins(
            request=None, placeholder=placeholder, template=None, lang=language
        )

        rendered_content = ""
        for plugin_instance in plugins:
            rendered_content += renderer.render_plugin(
                instance=plugin_instance,
                context={"request": None},
                placeholder=placeholder,
            )

        return rendered_content


def generate_search_document(page: Page):
    text = ""
    for placeholder in page.get_placeholders():
        text += PlaceholderRenderer.render_placeholder(placeholder)

    return text


# @override_settings(TEMPLATES=get_templates_settings())
class CmsPageIndexerTest(TestCase):
    """Unit tests for `ContactForm` CMS plugin"""

    def test_contact_form_plugin_render(self):
        description = "A description for the contactform"

        user = UserFactory()
        # page = create_page(
        #     title='Test Page',
        #     #template='INHERIT',
        #     template="c,sfullwidth.html",
        #     language='nl',
        #     created_by=user,
        #     published=True
        # )

        page = cms_tools.create_homepage()

        text = ""
        for placeholder in page.get_placeholders():
            add_plugin(
                placeholder,
                BannerTextPlugin,
                "nl",
            )
            text += PlaceholderRenderer.render_placeholder(placeholder)

        assert text == ""
        # form = ContactForm(user=user, request_session={})

        # html, context = cms_tools.render_plugin(
        #     ContactFormPlugin,
        #     plugin_data={"description": description},
        #     user=user,
        #     request_context={
        #         "form": form,
        #         "has_form_configuration": True,
        #     },
        # )

        # self.assertIn(f'<p class="utrecht-paragraph">{description}</p>', html)

    def test_approach_2(self):
        site = Site.objects.create(domain="http://test", name="testsite")
        page = cms_tools.create_homepage()
        pages = get_page_queryset(None)

        for page in pages:
            html = cms_tools.render_full_page(page)

            print(html)
            assert html == ""
