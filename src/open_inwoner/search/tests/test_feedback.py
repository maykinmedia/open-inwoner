import urllib

from django.contrib import messages
from django.test import override_settings, tag
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from furl import furl

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import CategoryFactory, ProductFactory, TagFactory

from ..models import Feedback
from .utils import ESMixin


@tag("elastic")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestFeedbackFunctionality(ESMixin, WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.product1 = ProductFactory.create(
            name="Name",
            summary="Some summary",
            content="Some content",
            keywords=["keyword1", "keyword2"],
        )
        self.update_index()

    def test_positive_feedback_is_saved_with_authenticated_user_and_without_filters(
        self,
    ):
        self.app.set_user(user=self.user)
        params = {"query": "keyword1"}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        self.assertNotEquals(response.context["paginator"].count, 0)
        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = "Some remark"
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.get()

        self.assertEqual(feedback.search_query, "query: keyword1")
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, "Some remark")
        self.assertEqual(feedback.searched_by, self.user)

    def test_negative_feedback_is_saved_with_authenticated_user_and_without_filters(
        self,
    ):
        self.app.set_user(user=self.user)
        params = {"query": "keyword1"}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = "Some remark"
        feedback_form["positive"] = "false"
        feedback_form.submit()

        feedback = Feedback.objects.get()

        self.assertEqual(feedback.search_query, "query: keyword1")
        self.assertEqual(feedback.search_url, url)
        self.assertFalse(feedback.positive)
        self.assertEqual(feedback.remark, "Some remark")
        self.assertEqual(feedback.searched_by, self.user)

    def test_positive_feedback_is_saved_with_unauthenticated_user_and_without_filters(
        self,
    ):
        params = {"query": "keyword1"}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = "Some remark"
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.get()

        self.assertEqual(feedback.search_query, "query: keyword1")
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, "Some remark")
        self.assertIsNone(feedback.searched_by)

    def test_negative_feedback_is_saved_with_unauthenticated_user_and_without_filters(
        self,
    ):
        params = {"query": "keyword1"}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = "Some remark"
        feedback_form["positive"] = "false"
        feedback_form.submit()

        feedback = Feedback.objects.get()

        self.assertEqual(feedback.search_query, "query: keyword1")
        self.assertEqual(feedback.search_url, url)
        self.assertFalse(feedback.positive)
        self.assertEqual(feedback.remark, "Some remark")
        self.assertIsNone(feedback.searched_by)

    def test_positive_feedback_is_saved_with_authenticated_user_and_with_filters(self):
        category1 = CategoryFactory()
        category2 = CategoryFactory()
        tag1 = TagFactory()
        tag2 = TagFactory()
        self.product1.tags.add(tag1, tag2)
        self.product1.categories.add(category1, category2)

        self.update_index()

        self.app.set_user(user=self.user)
        params = {
            "query": ["keyword1"],
            "categories": [category1.slug, category2.slug],
            "tags": [tag1.slug, tag2.slug],
        }
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = "Some remark"
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.get()

        self.assertEqual(
            feedback.search_query,
            f"query: keyword1 | categories: {category1.slug}, {category2.slug} | tags: {tag1.slug}, {tag2.slug}",
        )
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, "Some remark")
        self.assertEqual(feedback.searched_by, self.user)

    def test_positive_feedback_is_saved_with_unauthenticated_user_and_with_filters(
        self,
    ):
        params = {"query": "keyword1"}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = "Some remark"
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.get()

        self.assertEqual(feedback.search_query, "query: keyword1")
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, "Some remark")
        self.assertIsNone(feedback.searched_by)

    def test_feedback_form_not_displayed_after_submit(self):
        params = {"query": "keyword1"}
        url = furl(reverse("search:search")).add(params).url
        response = self.app.get(url)

        self.assertIsNotNone(response.html.find(id="feedback_form"))
        self.assertEqual(list(response.context["messages"]), [])

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = "Some remark"
        feedback_form["positive"] = "true"

        post_response = feedback_form.submit().follow()

        self.assertIsNone(post_response.html.find(id="feedback_form"))
        post_messages = list(post_response.context["messages"])
        self.assertEqual(len(post_messages), 1)

        message = post_messages[0]
        self.assertEqual(message.level, messages.SUCCESS)
        self.assertEqual(
            message.message,
            _(
                "Thank you for your feedback. It will help us to improve our search engine"
            ),
        )
