from django.test import TestCase

from cms.models import PageContent

from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openklant.cms_apps import OpenklantApphook

CONTACT_FORM_TEMPLATE = "cms/contactform/form_outer.html"
DEFAULT_TEMPLATE = "cms/fullwidth.html"


def get_page_content(page) -> PageContent:
    return PageContent._original_manager.get(page=page, language="nl")


class ApphookPageTemplateTests(TestCase):
    def test_apphook_page_created_with_template_of_apphook(self):
        page = cms_tools.create_apphook_page(OpenklantApphook)

        self.assertEqual(get_page_content(page).template, CONTACT_FORM_TEMPLATE)

    def test_apphook_page_without_template_of_apphook_uses_default(self):
        page = cms_tools.create_apphook_page(CollaborateApphook)

        self.assertEqual(get_page_content(page).template, DEFAULT_TEMPLATE)

    def test_template_of_apphook_page_can_be_changed(self):
        page = cms_tools.create_apphook_page(OpenklantApphook, publish=False)
        page_content = get_page_content(page)

        page_content.template = DEFAULT_TEMPLATE
        page_content.save()

        page_content.refresh_from_db()
        self.assertEqual(page_content.template, DEFAULT_TEMPLATE)
