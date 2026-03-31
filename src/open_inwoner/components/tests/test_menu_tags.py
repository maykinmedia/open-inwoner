from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import ImproperlyConfigured
from django.template import Context
from django.test import RequestFactory, TestCase, override_settings
from django.urls import NoReverseMatch, Resolver404, resolve
from django.utils import translation

from cms import api
from cms.models import PageContent
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.toolbar import CMSToolbar
from djangocms_versioning.constants import DRAFT
from djangocms_versioning.models import Version

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.extensions.constants import IndicatorChoices
from open_inwoner.cms.extensions.models import CommonExtension
from open_inwoner.cms.tests.cms_tools import publish_page
from open_inwoner.components.templatetags.menu import (
    SideNavMenuData,
    react_sidenav_data,
)


@override_settings(
    CMS_PERMISSION=False,
    ROOT_URLCONF="open_inwoner.components.tests.test_urls",
    LANGUAGE_CODE="nl",
    LANGUAGES=[("nl", "Dutch"), ("en", "English")],
    USE_I18N=True,
)
class TestSideNavigationMenuFactory(CMSTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.regular_user = UserFactory(is_staff=False)
        self.staff_user = UserFactory(is_staff=True)

        # Create home page with correct reverse_id
        self.home_page = api.create_page(
            "Home",
            "cms/fullwidth.html",
            "nl",
            reverse_id="home",
            in_navigation=True,
            slug="home",
        )
        publish_page(self.home_page, "nl")

    def _get_menu_data(self, user, path="/"):
        with translation.override("nl"):
            request = self.factory.get(path)
            request.user = user
            request.session = SessionStore()
            request.session.create()
            request.toolbar = CMSToolbar(request)

            # Simulate Django's URL resolution middleware
            try:
                request.resolver_match = resolve(path)
            except Resolver404:
                request.resolver_match = None

            context = Context({"request": request})
            return react_sidenav_data(context)

    def test_menu_icons_from_draft_page_common_extension(self):
        page_with_icon = api.create_page(
            "Page With Icon",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(page_with_icon, "nl")

        # Add CommonExtension to the draft version
        CommonExtension.objects.create(
            extended_object=page_with_icon,  # This is the draft version
            menu_icon="person",
        )

        # Regular user should see published page with icon
        regular_menu = self._get_menu_data(self.regular_user)
        expected_regular_menu = [
            {
                "href": page_with_icon.get_absolute_url(),
                "label": "Page With Icon",
                "icon": "person",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            regular_menu,
            expected_regular_menu,
            msg="Regular user should see published page with icon from draft version CommonExtension",
        )

        # Staff user should see the same
        staff_menu = self._get_menu_data(self.staff_user)
        expected_staff_menu = [
            {
                "href": page_with_icon.get_absolute_url(),
                "label": "Page With Icon",
                "icon": "person",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            staff_menu,
            expected_staff_menu,
            msg="Staff user should see same icon from draft version",
        )

    def test_menu_pages_without_common_extension_show_no_icon(self):
        page_without_icon = api.create_page(
            "Page Without Icon",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(page_without_icon, "nl")
        # Intentionally avoid creating a CommonExtension

        # Regular user should see page with null icon
        regular_menu = self._get_menu_data(self.regular_user)
        expected_regular_menu = [
            {
                "href": page_without_icon.get_absolute_url(),
                "label": "Page Without Icon",
                "icon": None,
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            regular_menu,
            expected_regular_menu,
            msg="Page without CommonExtension should show no icon",
        )

        # Staff user should see the same structure
        staff_menu = self._get_menu_data(self.staff_user)
        expected_staff_menu = [
            {
                "href": page_without_icon.get_absolute_url(),
                "label": "Page Without Icon",
                "icon": None,
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            staff_menu,
            expected_staff_menu,
            msg="Staff should see same structure with no icon",
        )

    def test_menu_icon_fallback_between_draft_and_public_versions(self):
        # Create page with icon on draft (most common)
        page_draft_icon = api.create_page(
            "Page Draft Icon",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(page_draft_icon, "nl")

        CommonExtension.objects.create(
            extended_object=page_draft_icon,
            menu_icon="draft_icon",
        )

        # Regular user should see icon from draft version CommonExtension
        regular_menu = self._get_menu_data(self.regular_user)
        expected_regular_menu = [
            {
                "href": page_draft_icon.get_absolute_url(),
                "label": "Page Draft Icon",
                "icon": "draft_icon",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            regular_menu,
            expected_regular_menu,
            msg="Regular user should see icon found via fallback to draft version",
        )

        # Staff user should see the same complete structure
        staff_menu = self._get_menu_data(self.staff_user)
        expected_staff_menu = [
            {
                "href": page_draft_icon.get_absolute_url(),
                "label": "Page Draft Icon",
                "icon": "draft_icon",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            staff_menu,
            expected_staff_menu,
            msg="Staff user should see same fallback behavior as regular user",
        )

    def test_menu_counters_are_calculated_from_user_specific_data(self):
        # Create page with inbox message indicator
        inbox_page = api.create_page(
            "My Messages",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(inbox_page, "nl")

        CommonExtension.objects.create(
            extended_object=inbox_page,
            menu_indicator=IndicatorChoices.inbox_new_messages,
        )

        # Set up user to have 7 new messages
        self.regular_user.get_new_messages_total = lambda: 7

        menu_data = self._get_menu_data(self.regular_user)
        expected_menu = [
            {
                "href": inbox_page.get_absolute_url(),
                "label": "My Messages",
                "icon": None,
                "current": False,
                "counter": 7,
            }
        ]
        self.assertEqual(
            menu_data,
            expected_menu,
            msg="Counter should match user's message count",
        )

    def test_current_page_is_highlighted_when_user_visits_that_page(self):
        # Create two pages to test current detection
        visited_page = api.create_page(
            "Visited Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
            slug="visited-page",
        )
        publish_page(visited_page, "nl")

        other_page = api.create_page(
            "Other Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
            slug="other-page",
        )
        publish_page(other_page, "nl")

        visited_page_url = visited_page.get_absolute_url()
        menu_data = self._get_menu_data(self.regular_user, path=visited_page_url)

        expected_menu = [
            {
                "href": visited_page.get_absolute_url(),
                "label": "Visited Page",
                "icon": None,
                "current": True,
                "counter": None,
            },
            {
                "href": other_page.get_absolute_url(),
                "label": "Other Page",
                "icon": None,
                "current": False,
                "counter": None,
            },
        ]
        self.assertEqual(
            menu_data,
            expected_menu,
            msg="Visited page should be marked as current, other page should not",
        )

    def _make_request(self, user, path="/"):
        request = self.factory.get(path)
        request.user = user
        request.session = SessionStore()
        request.session.create()
        request.toolbar = CMSToolbar(request)
        return request

    def _downgrade_to_draft(self, page, language="nl"):
        """
        Force the published Version for page/language back to DRAFT state,
        bypassing FSM transitions. This simulates a page that was never published
        (or whose published version was retracted) so that only a DRAFT version
        remains. Used to set up draft-visibility test scenarios.
        """
        ct = ContentType.objects.get_for_model(PageContent)
        Version.objects.filter(
            content_type=ct,
            object_id__in=PageContent._original_manager.filter(
                page=page, language=language
            ).values("pk"),
        ).update(state=DRAFT)

    def test_draft_page_not_visible_to_regular_users_but_visible_to_staff(self):
        """
        _is_visible_to_user filters out draft pages for regular users but
        allows staff through. Tested directly on _is_visible_to_user because
        the CMS 4.1.x default menu (outside edit mode) only delivers published
        nodes, so draft pages never reach _is_visible_to_user via the full stack.
        """
        from unittest.mock import MagicMock

        page = api.create_page(
            "Draft Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(page, "nl")
        self._downgrade_to_draft(page)

        node = MagicMock()
        node.id = page.pk

        with translation.override("nl"):
            regular_request = self._make_request(self.regular_user)
            self.assertFalse(
                SideNavMenuData(
                    Context({"request": regular_request})
                )._is_visible_to_user(node),
                msg="Regular user must not see a draft-only page",
            )

            staff_request = self._make_request(self.staff_user)
            self.assertTrue(
                SideNavMenuData(
                    Context({"request": staff_request})
                )._is_visible_to_user(node),
                msg="Staff user must see a draft-only page",
            )

    def test_menu_icons_on_draft_only_pages_are_visible_to_staff(self):
        """See test_draft_page_not_visible_to_regular_users_but_visible_to_staff
        for why we test _is_visible_to_user and _extract_icon directly."""
        from unittest.mock import MagicMock

        page = api.create_page(
            "Draft Page With Icon",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(page, "nl")
        CommonExtension.objects.create(extended_object=page, menu_icon="edit")
        self._downgrade_to_draft(page)

        node = MagicMock()
        node.id = page.pk

        with translation.override("nl"):
            staff_request = self._make_request(self.staff_user)
            menu_data = SideNavMenuData(Context({"request": staff_request}))

            self.assertTrue(
                menu_data._is_visible_to_user(node),
                msg="Staff user must see a draft-only page",
            )
            self.assertEqual(
                menu_data._extract_icon(node),
                "edit",
                msg="Staff user must see icon on a draft-only page",
            )

    def test_pages_only_published_in_other_languages_are_hidden_from_menu(self):
        dutch_page = api.create_page(
            "Dutch Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(dutch_page, "nl")

        en_page = api.create_page(
            "English Only Page",
            "cms/fullwidth.html",
            "en",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(en_page, "en")  # Only publish in English, not Dutch

        # Menu in Dutch context should only contain Dutch page
        menu_data = self._get_menu_data(self.regular_user)
        expected_menu = [
            {
                "href": dutch_page.get_absolute_url(),
                "label": "Dutch Page",
                "icon": None,
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            menu_data,
            expected_menu,
            msg="Menu in Dutch context should only contain Dutch page",
        )

    def test_invalid_counter_values_are_handled_gracefully(self):
        page_with_broken_counter = api.create_page(
            "Broken Counter Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        publish_page(page_with_broken_counter, "nl")

        CommonExtension.objects.create(
            extended_object=page_with_broken_counter,
            menu_indicator=IndicatorChoices.inbox_new_messages,
        )

        # Set up user method to return invalid (non-integer) value
        self.regular_user.get_new_messages_total = lambda: "not-a-number"

        # Menu should still generate successfully with counter as None
        menu_data = self._get_menu_data(self.regular_user)
        expected_menu = [
            {
                "href": page_with_broken_counter.get_absolute_url(),
                "label": "Broken Counter Page",
                "icon": None,
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            menu_data,
            expected_menu,
            msg="Counter should be None when conversion fails",
        )

    def test_missing_home_page_raises_configuration_error(self):
        self.home_page.delete()

        request = self.factory.get("/")
        request.user = self.regular_user
        request.toolbar = CMSToolbar(request)
        context = Context({"request": request})

        with self.assertRaisesRegex(
            ImproperlyConfigured,
            "You must define a root CMS page with reverse_id='home'",
        ):
            SideNavMenuData(context).get_menu_data()


class TestExtraMenuItemGeneration(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_faq_menu_item_is_added_when_context_indicates_faq_available(self):
        request = self.factory.get("/some-other-page/")
        context = Context({"request": request, "has_general_faq_questions": True})

        extra_items = SideNavMenuData(context).get_extra_menu_items()

        expected_faq_item = {
            "href": "/faq/",  # Based on reverse("general_faq")
            "label": "Veelgestelde vragen",
            "icon": "question_answer",
            "current": False,
            "counter": None,
        }
        self.assertEqual(
            extra_items,
            [expected_faq_item],
            msg="FAQ item should be added when context indicates FAQ available",
        )

    def test_faq_menu_item_is_marked_current_when_user_is_on_faq_page(self):
        request = self.factory.get("/faq/some-question/")
        context = Context({"request": request, "has_general_faq_questions": True})

        extra_items = SideNavMenuData(context).get_extra_menu_items()

        expected_faq_item = {
            "href": "/faq/",
            "label": "Veelgestelde vragen",
            "icon": "question_answer",
            "current": True,
            "counter": None,
        }
        self.assertEqual(
            extra_items,
            [expected_faq_item],
            msg="FAQ item should be marked current when user is on FAQ page",
        )

    def test_no_extra_items_when_faq_not_available(self):
        context_false = Context(
            {"request": self.factory.get("/"), "has_general_faq_questions": False}
        )
        self.assertEqual(SideNavMenuData(context_false).get_extra_menu_items(), [])

        # Test with missing key
        context_missing = Context({"request": self.factory.get("/")})
        self.assertEqual(SideNavMenuData(context_missing).get_extra_menu_items(), [])

    def test_faq_item_without_request_in_context_defaults_to_not_current(self):
        context = Context({"has_general_faq_questions": True})

        with self.assertRaises(ValueError):
            SideNavMenuData(context).get_extra_menu_items()

    def test_url_reverse_failures_are_handled_gracefully(self):
        context = Context(
            {"request": self.factory.get("/"), "has_general_faq_questions": True}
        )

        with patch("open_inwoner.components.templatetags.menu.reverse") as mock_reverse:
            mock_reverse.side_effect = NoReverseMatch(
                "general_faq URL pattern not found"
            )

            extra_items = SideNavMenuData(context).get_extra_menu_items()
            self.assertEqual(
                extra_items,
                [],
                msg="Should return empty list on URL failure",
            )
