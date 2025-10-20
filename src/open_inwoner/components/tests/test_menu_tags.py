from unittest.mock import patch

from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import ImproperlyConfigured
from django.template import Context
from django.test import RequestFactory, TestCase, override_settings
from django.urls import NoReverseMatch, Resolver404, resolve
from django.utils import translation

from cms import api
from cms.test_utils.testcases import CMSTestCase

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.extensions.constants import IndicatorChoices
from open_inwoner.cms.extensions.models import CommonExtension
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
        self.home_page.publish("nl")

    def _get_menu_data(self, user, path="/"):
        with translation.override("nl"):
            request = self.factory.get(path)
            request.user = user
            request.session = SessionStore()
            request.session.create()

            # Simulate Django's URL resolution middleware
            try:
                request.resolver_match = resolve(path)
            except Resolver404:
                request.resolver_match = None

            context = Context({"request": request})
            return react_sidenav_data(context)

    def test_draft_page_visibility_differs_for_staff_and_regular_users(self):
        published_page = api.create_page(
            "Published Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        published_page.publish("nl")

        draft_page = api.create_page(
            "Draft Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        # Don't publish this page - keep it as true draft

        # Regular user should only see the published page
        regular_user_menu = self._get_menu_data(self.regular_user)
        expected_regular_menu = [
            {
                "href": published_page.get_absolute_url(),
                "label": "Published Page",
                "icon": None,
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(regular_user_menu, expected_regular_menu)

        # Staff user should see both published and draft pages
        staff_user_menu = self._get_menu_data(self.staff_user)
        expected_staff_menu = [
            {
                "href": published_page.get_absolute_url(),
                "label": "Published Page",
                "icon": None,
                "current": False,
                "counter": None,
            },
            {
                "href": draft_page.get_absolute_url(),
                "label": "Draft Page",
                "icon": None,
                "current": False,
                "counter": None,
            },
        ]
        self.assertEqual(staff_user_menu, expected_staff_menu)

    def test_menu_icons_from_draft_page_common_extension(self):
        page_with_icon = api.create_page(
            "Page With Icon",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        page_with_icon.publish("nl")

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

    def test_menu_icons_on_draft_only_pages_for_staff(self):
        draft_page = api.create_page(
            "Draft Page With Icon",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        # Don't publish this page - keep as draft only

        CommonExtension.objects.create(
            extended_object=draft_page,
            menu_icon="edit",
        )

        # Regular user should not see any pages
        regular_menu = self._get_menu_data(self.regular_user)
        self.assertEqual(regular_menu, [])

        # Staff user should see the draft page with complete menu structure
        staff_menu = self._get_menu_data(self.staff_user)
        expected_staff_menu = [
            {
                "href": draft_page.get_absolute_url(),
                "label": "Draft Page With Icon",
                "icon": "edit",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(
            staff_menu,
            expected_staff_menu,
            msg="Staff user should see draft page with icon from CommonExtension",
        )

    def test_menu_pages_without_common_extension_show_no_icon(self):
        page_without_icon = api.create_page(
            "Page Without Icon",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        page_without_icon.publish("nl")
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
        page_draft_icon.publish("nl")

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
        inbox_page.publish("nl")

        # Get the published version of the page
        published_page = inbox_page.get_public_object()

        CommonExtension.objects.create(
            extended_object=published_page,
            menu_indicator=IndicatorChoices.inbox_new_messages,
        )

        # Set up user to have 7 new messages
        self.regular_user.get_new_messages_total = lambda: 7

        menu_data = self._get_menu_data(self.regular_user)
        expected_menu = [
            {
                "href": published_page.get_absolute_url(),
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
        visited_page.publish("nl")

        other_page = api.create_page(
            "Other Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
            slug="other-page",
        )
        other_page.publish("nl")

        published_visited_page = visited_page.get_public_object()
        published_other_page = other_page.get_public_object()

        visited_page_url = published_visited_page.get_absolute_url()
        menu_data = self._get_menu_data(self.regular_user, path=visited_page_url)

        expected_menu = [
            {
                "href": published_visited_page.get_absolute_url(),
                "label": "Visited Page",
                "icon": None,
                "current": True,
                "counter": None,
            },
            {
                "href": published_other_page.get_absolute_url(),
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

    def test_pages_only_published_in_other_languages_are_hidden_from_menu(self):
        dutch_page = api.create_page(
            "Dutch Page",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
        )
        dutch_page.publish("nl")

        en_page = api.create_page(
            "English Only Page",
            "cms/fullwidth.html",
            "en",
            parent=self.home_page,
            in_navigation=True,
        )
        en_page.publish("en")  # Only publish in English, not Dutch

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
        page_with_broken_counter.publish("nl")

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
