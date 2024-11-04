from django_webtest import WebTest

from open_inwoner.cms.benefits.cms_apps import SSDApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.inbox.cms_apps import InboxApphook
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests.cms_tools import create_apphook_page
from open_inwoner.cms.utils.page_display import (
    benefits_page_is_published,
    case_page_is_published,
    collaborate_page_is_published,
    get_active_app_names,
    inbox_page_is_published,
    profile_page_is_published,
)


class CMSPageDisplayTests(WebTest):
    def test_published_pages_helpers(self):
        # check blank
        names = get_active_app_names()
        self.assertEqual(names, list())

        self.assertFalse(inbox_page_is_published())
        self.assertFalse(case_page_is_published())
        self.assertFalse(collaborate_page_is_published())
        self.assertFalse(benefits_page_is_published())
        self.assertFalse(profile_page_is_published())

        # check apps
        inbox = create_apphook_page(InboxApphook)
        self.assertTrue(inbox_page_is_published())
        self.assertEqual(set(get_active_app_names()), {"inbox"})

        create_apphook_page(CasesApphook)
        self.assertTrue(case_page_is_published())
        self.assertEqual(set(get_active_app_names()), {"inbox", "cases"})

        create_apphook_page(CollaborateApphook)
        self.assertTrue(collaborate_page_is_published())
        self.assertEqual(set(get_active_app_names()), {"inbox", "cases", "collaborate"})

        create_apphook_page(SSDApphook)
        self.assertTrue(benefits_page_is_published())
        self.assertEqual(
            set(get_active_app_names()), {"inbox", "cases", "collaborate", "ssd"}
        )

        create_apphook_page(ProfileApphook)
        self.assertTrue(benefits_page_is_published())
        self.assertEqual(
            set(get_active_app_names()),
            {"inbox", "cases", "collaborate", "ssd", "profile"},
        )

        # check unpublishing
        inbox.unpublish("nl")
        self.assertFalse(inbox_page_is_published())
        self.assertEqual(
            set(get_active_app_names()),
            {"cases", "collaborate", "ssd", "profile"},
        )
