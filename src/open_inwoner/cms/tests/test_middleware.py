from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from cms.models import PageContent
from djangocms_versioning.constants import DRAFT, PUBLISHED
from djangocms_versioning.models import Version
from maykin_2fa.test import disable_admin_mfa
from pyquery import PyQuery

from open_inwoner.cms.tests import cms_tools
from open_inwoner.cms.utils.middleware import DropToolbarMiddleware
from open_inwoner.utils.tests.helpers import TwoFactorUserTestMixin


class TestDropToolbarMiddleware(TwoFactorUserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cms_tools.create_homepage()
        cls.url = reverse("pages-root")

    def test_middleware_is_mounted(self):
        cls = DropToolbarMiddleware
        path = f"{cls.__module__}.{cls.__name__}"
        self.assertIn(path, settings.MIDDLEWARE)

    def test_anon_shows_no_toolbar(self):
        response = self.client.get(self.url)

        self.assertNotHasToolbar(response)

    @disable_admin_mfa()
    def test_not_staff_not_verified_no_2fa_shows_no_toolbar(self):
        self.create_user()
        self.login_user()
        response = self.client.get(self.url)

        self.assertNotHasToolbar(response)

    @disable_admin_mfa()
    def test_staff_not_verified_no_2fa_shows_toolbar(self):
        self.create_user(is_staff=True)
        self.login_user()
        response = self.client.get(self.url)

        self.assertHasToolbar(response)

    @override_settings(MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS=[])
    def test_staff_not_verified_with_2fa_shows_no_toolbar(self):
        self.create_user(is_staff=True)
        self.login_user()
        response = self.client.get(self.url)

        self.assertNotHasToolbar(response)

    def test_staff_verified_with_2fa_shows_toolbar(self):
        self.create_user(is_staff=True)
        self.enable_otp()
        self.login_user()
        response = self.client.get(self.url)

        self.assertHasToolbar(response)

    def assertHasToolbar(self, response):
        d = PyQuery(response.content.decode("utf8"))
        if not len(d(".cms-toolbar")):
            self.fail("cannot locate element with class '.cms-toolbar'")

    def assertNotHasToolbar(self, response):
        d = PyQuery(response.content.decode("utf8"))
        if len(d(".cms-toolbar")):
            self.fail("found element with class '.cms-toolbar'")


class TestDropToolbarMiddlewareVersionSelection(TestCase):
    """
    Test that DropToolbarMiddleware passes the correct PageContent version to
    toolbar.set_object().

    In public mode only the PUBLISHED version should be used. In edit/preview
    mode the DRAFT version takes priority (falling back to PUBLISHED when no
    draft exists). Without this, pages with multiple versions would always
    render content from the oldest PageContent row (lowest PK).
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.homepage = cms_tools.create_homepage()

    # -- helpers ----------------------------------------------------------

    def _set_version_state(self, state):
        """Force the homepage version into a given state, bypassing FSM."""
        ct = ContentType.objects.get_for_model(PageContent)
        Version.objects.filter(
            content_type=ct,
            object_id__in=PageContent._original_manager.filter(
                page=self.homepage, language="nl"
            ).values("pk"),
        ).update(state=state)

    def _get_page_content_for_state(self, state):
        ct = ContentType.objects.get_for_model(PageContent)
        version = Version.objects.filter(
            content_type=ct,
            object_id__in=PageContent._original_manager.filter(
                page=self.homepage, language="nl"
            ).values("pk"),
            state=state,
        ).first()

        return (
            PageContent._original_manager.get(pk=version.object_id) if version else None
        )

    def _run_middleware(self, *, edit_mode=False):
        """
        Run DropToolbarMiddleware against the homepage with a mock toolbar.
        Returns the PageContent passed to toolbar.set_object(), or None.
        """
        mock_toolbar = MagicMock()
        mock_toolbar.edit_mode_active = edit_mode
        mock_toolbar.preview_mode_active = False

        mock_user = MagicMock()
        mock_user.is_staff = True
        mock_user.is_verified.return_value = True

        mock_request = MagicMock()
        mock_request.user = mock_user
        mock_request.current_page = self.homepage
        mock_request.session = {}

        middleware = DropToolbarMiddleware(get_response=lambda r: MagicMock())

        with patch(
            "open_inwoner.cms.utils.middleware.get_toolbar_from_request",
            return_value=mock_toolbar,
        ):
            with patch(
                "open_inwoner.cms.utils.middleware.get_language", return_value="nl"
            ):
                middleware(mock_request)

        if mock_toolbar.set_object.called:
            return mock_toolbar.set_object.call_args[0][0]
        return None

    # -- tests ------------------------------------------------------------

    def test_public_mode_uses_published_page_content(self):
        published_pc = self._get_page_content_for_state(PUBLISHED)
        self.assertEqual(self._run_middleware(edit_mode=False), published_pc)

    def test_public_mode_ignores_page_with_only_draft_version(self):
        self._set_version_state(DRAFT)
        self.assertIsNone(self._run_middleware(edit_mode=False))

    def test_edit_mode_uses_draft_page_content(self):
        self._set_version_state(DRAFT)
        draft_pc = self._get_page_content_for_state(DRAFT)
        self.assertEqual(self._run_middleware(edit_mode=True), draft_pc)

    def test_edit_mode_falls_back_to_published_when_no_draft_exists(self):
        published_pc = self._get_page_content_for_state(PUBLISHED)
        self.assertEqual(self._run_middleware(edit_mode=True), published_pc)
