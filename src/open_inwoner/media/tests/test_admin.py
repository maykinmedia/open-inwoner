from django.urls import reverse

from cms.utils.permissions import set_current_user
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory

from .factories import VideoFactory


@disable_admin_mfa()
class VideoAdminTests(WebTest):
    def setUp(self):
        set_current_user(
            None
        )  # otherwise will assume previous user is logged in (who is often deleted after test)
        return super().setUp()

    def test_get_changelist(self):
        user = UserFactory(is_staff=True, is_superuser=True)
        url = reverse("admin:media_video_changelist")
        response = self.app.get(url, user=user)
        self.assertEqual(response.status_code, 200)

    def test_get_changelist_with_videos(self):
        video = VideoFactory()
        user = UserFactory(is_staff=True, is_superuser=True)
        url = reverse("admin:media_video_changelist")
        response = self.app.get(url, user=user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, video.link_id)
        self.assertContains(response, video.external_url)

    def test_get_change(self):
        video = VideoFactory()
        user = UserFactory(is_staff=True, is_superuser=True)
        url = reverse("admin:media_video_change", kwargs={"object_id": video.id})
        response = self.app.get(url, user=user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, video.link_id)
        self.assertContains(response, video.external_url)
