from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.html import escape

from cms import api
from cms.models import PageContent
from cms.utils.permissions import set_current_user
from django_webtest import WebTest
from djangocms_versioning.constants import ARCHIVED, DRAFT, PUBLISHED, UNPUBLISHED
from djangocms_versioning.helpers import version_list_url
from djangocms_versioning.models import Version
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory


@disable_admin_mfa()
class VersionAdminTest(WebTest):
    """
    The concrete Version model is registered so that admin listings of related
    objects link to it, most importantly the user deletion confirmation.
    """

    def setUp(self):
        # otherwise cms assumes the previous user is logged in, who is often deleted
        set_current_user(None)
        super().setUp()
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)

    def _create_version(self, author, state=DRAFT, title="Foo", language="nl"):
        page = api.create_page(
            title, "cms/fullwidth.html", language, created_by=author, in_navigation=True
        )
        page_content = PageContent._original_manager.get(page=page, language=language)
        version = Version.objects.get(
            content_type=ContentType.objects.get_for_model(PageContent),
            object_id=page_content.pk,
        )
        Version.objects.filter(pk=version.pk).update(created_by=author)

        if state == PUBLISHED:
            version.publish(author)
        elif state == ARCHIVED:
            version.archive(author)
        elif state == UNPUBLISHED:
            version.publish(author)
            version.unpublish(author)

        # re-fetch rather than refresh_from_db: that assigns to every field, and
        # `state` rejects assignment, so it would raise
        return page, Version.objects.get(pk=version.pk)

    def test_user_delete_confirmation_links_to_version(self):
        author = UserFactory(is_staff=True)
        page, version = self._create_version(author)

        url = reverse("admin:accounts_user_delete", kwargs={"object_id": author.pk})
        response = self.app.get(url, user=self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse(
                "admin:djangocms_versioning_version_change",
                kwargs={"object_id": version.pk},
            ),
        )

    def test_user_delete_confirmation_reports_versions_as_protected(self):
        """
        Version.created_by is PROTECT, so the versions must show up as protected
        rather than as a permissions problem.
        """
        author = UserFactory(is_staff=True)
        self._create_version(author)

        url = reverse("admin:accounts_user_delete", kwargs={"object_id": author.pk})
        response = self.app.get(url, user=self.admin_user)

        self.assertTrue(response.context["protected"])
        self.assertFalse(response.context["perms_lacking"])

    def test_version_detail_identifies_the_page_it_belongs_to(self):
        author = UserFactory(is_staff=True)
        page, version = self._create_version(author, title="Findable page")

        url = reverse(
            "admin:djangocms_versioning_version_change",
            kwargs={"object_id": version.pk},
        )
        response = self.app.get(url, user=self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Findable page")
        self.assertContains(response, escape(version_list_url(version.content)))

    def test_version_detail_is_read_only(self):
        author = UserFactory(is_staff=True)
        page, version = self._create_version(author)

        url = reverse(
            "admin:djangocms_versioning_version_change",
            kwargs={"object_id": version.pk},
        )
        response = self.app.get(url, user=self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="_save"')

    def test_delete_button_hidden_for_draft_and_published(self):
        for state in (DRAFT, PUBLISHED):
            with self.subTest(state=state):
                author = UserFactory(is_staff=True)
                page, version = self._create_version(author, state=state)

                url = reverse(
                    "admin:djangocms_versioning_version_change",
                    kwargs={"object_id": version.pk},
                )
                response = self.app.get(url, user=self.admin_user)

                self.assertNotContains(
                    response,
                    reverse(
                        "admin:djangocms_versioning_version_delete",
                        kwargs={"object_id": version.pk},
                    ),
                )

    def test_delete_button_shown_for_archived_and_unpublished(self):
        for state in (ARCHIVED, UNPUBLISHED):
            with self.subTest(state=state):
                author = UserFactory(is_staff=True)
                page, version = self._create_version(author, state=state)

                url = reverse(
                    "admin:djangocms_versioning_version_change",
                    kwargs={"object_id": version.pk},
                )
                response = self.app.get(url, user=self.admin_user)

                self.assertContains(
                    response,
                    reverse(
                        "admin:djangocms_versioning_version_delete",
                        kwargs={"object_id": version.pk},
                    ),
                )

    def test_deleting_draft_or_published_version_is_refused(self):
        for state in (DRAFT, PUBLISHED):
            with self.subTest(state=state):
                author = UserFactory(is_staff=True)
                page, version = self._create_version(author, state=state)

                url = reverse(
                    "admin:djangocms_versioning_version_delete",
                    kwargs={"object_id": version.pk},
                )
                response = self.app.get(url, user=self.admin_user)

                self.assertRedirects(
                    response,
                    reverse(
                        "admin:djangocms_versioning_version_change",
                        kwargs={"object_id": version.pk},
                    ),
                )
                self.assertTrue(Version.objects.filter(pk=version.pk).exists())

    def test_deleting_archived_or_unpublished_version_is_allowed(self):
        for state in (ARCHIVED, UNPUBLISHED):
            with self.subTest(state=state):
                author = UserFactory(is_staff=True)
                page, version = self._create_version(author, state=state)

                url = reverse(
                    "admin:djangocms_versioning_version_delete",
                    kwargs={"object_id": version.pk},
                )
                response = self.app.get(url, user=self.admin_user)

                self.assertEqual(response.status_code, 200)

    @override_settings(DJANGOCMS_VERSIONING_ALLOW_DELETING_VERSIONS=False)
    def test_delete_button_hidden_when_deleting_versions_is_disabled(self):
        author = UserFactory(is_staff=True)
        page, version = self._create_version(author, state=ARCHIVED)

        url = reverse(
            "admin:djangocms_versioning_version_change",
            kwargs={"object_id": version.pk},
        )
        response = self.app.get(url, user=self.admin_user)

        self.assertNotContains(
            response,
            reverse(
                "admin:djangocms_versioning_version_delete",
                kwargs={"object_id": version.pk},
            ),
        )

    @override_settings(DJANGOCMS_VERSIONING_ALLOW_DELETING_VERSIONS=False)
    def test_deleting_is_refused_when_deleting_versions_is_disabled(self):
        """
        Otherwise this admin would be a way around the project wide kill switch,
        which is checked by djangocms-versioning but only on its own version admin.
        """
        author = UserFactory(is_staff=True)
        page, version = self._create_version(author, state=ARCHIVED)

        url = reverse(
            "admin:djangocms_versioning_version_delete",
            kwargs={"object_id": version.pk},
        )
        response = self.app.get(url, user=self.admin_user)

        self.assertRedirects(
            response,
            reverse(
                "admin:djangocms_versioning_version_change",
                kwargs={"object_id": version.pk},
            ),
        )
        self.assertTrue(Version.objects.filter(pk=version.pk).exists())

    def test_changelist_renders(self):
        """
        The changelist is not linked anywhere but stays reachable by url. Django
        resolves its template by app label, which lands on the one djangocms-versioning
        ships for its own version admin and cannot render from here.
        """
        author = UserFactory(is_staff=True)
        self._create_version(author)

        url = reverse("admin:djangocms_versioning_version_changelist")
        response = self.app.get(url, user=self.admin_user)

        self.assertEqual(response.status_code, 200)

    def test_no_bulk_actions_offered(self):
        """
        The changelist is unlinked but reachable; its bulk delete would bypass
        the per-version state check.
        """
        request = RequestFactory().get("/")
        request.user = self.admin_user
        model_admin = admin.site.get_model_admin(Version)

        self.assertEqual(model_admin.get_actions(request), {})
