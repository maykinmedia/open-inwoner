from django.template import RequestContext, Template
from django.test import TestCase, override_settings
from django.utils import translation

from cms.api import add_plugin
from cms.models import PageContent, Placeholder
from cms.toolbar.utils import get_object_edit_url, get_object_structure_url
from django_prosemirror.constants import get_empty_doc
from djangocms_versioning.models import Version
from maykin_2fa.test import disable_admin_mfa
from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.tests import cms_tools


@disable_admin_mfa()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class PageContentObjectToolbarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # see the helper's docstring: otherwise versioning can't find the versions
        cms_tools.reset_versionables_content_type_cache()

        cls.user = UserFactory(is_staff=True, is_superuser=True)
        cms_tools.create_homepage()
        # the apphook only resolves once the page is published
        cls.page = cms_tools.create_apphook_page(ProductsApphook)
        cls.published = PageContent.admin_manager.get(page=cls.page, language="nl")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_live_apphook_page_offers_editing(self):
        response = self.client.get(self.page.get_absolute_url("nl"))

        self.assertEqual(response.status_code, 200)
        doc = PyQuery(response.content)
        self.assertEqual(len(doc(".cms-versioning-js-edit-btn")), 1)

    def test_editing_apphook_page_offers_structure_mode_and_publishing(self):
        # an editor clicking "Edit" on a published page gets a new draft
        draft = Version.objects.get_for_content(self.published).copy(self.user).content

        response = self.client.get(get_object_edit_url(draft, language="nl"))

        self.assertEqual(response.status_code, 200)
        doc = PyQuery(response.content)
        mode_switcher = doc(".cms-toolbar-item-cms-mode-switcher a")
        self.assertIn(
            get_object_structure_url(draft),
            [link.attrib["href"] for link in mode_switcher],
        )
        self.assertEqual(len(doc(".cms-versioning-js-publish-btn")), 1)


class ApphookPagePlaceholderTests(TestCase):
    """
    Visitors get no toolbar object, so placeholders on apphook pages have to come
    from the published content without one.
    """

    def setUp(self):
        super().setUp()
        cms_tools.reset_versionables_content_type_cache()
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.page = cms_tools.create_apphook_page(ProductsApphook)

    def add_text(self, page_content: PageContent, text: str):
        placeholder = Placeholder.objects.get_for_obj(page_content).get(
            slot="banner_text"
        )
        plugin = add_plugin(
            placeholder=placeholder,
            plugin_type="TextPlugin",
            language="nl",
            body=get_empty_doc(),
        )
        plugin.body.html = f"<p>{text}</p>"
        plugin.save()

    def test_visitor_sees_published_version_of_placeholder(self):
        first = PageContent.admin_manager.get(page=self.page, language="nl")
        first_version = Version.objects.get_for_content(first)
        second = first_version.copy(self.user).content
        self.add_text(second, "Tweede versie")
        # archives the first version
        Version.objects.get_for_content(second).publish(self.user)

        request = cms_tools.get_request(page=self.page)
        template = Template("{% load cms_tags %}{% placeholder 'banner_text' %}")
        with translation.override("nl"):
            rendered = template.render(RequestContext(request))

        self.assertIn("Tweede versie", rendered)
