import urllib

from django.contrib import messages
from django.test import tag
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from furl import furl

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import CategoryFactory, TagFactory

from ..models import Feedback
from .factories import FeedbackFactory
from .utils import ESMixin


@tag("elastic")
class TestFeedbackFunctionality(ESMixin, WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.feedback = FeedbackFactory.build()
        self.category1 = CategoryFactory.build()
        self.category2 = CategoryFactory.build()
        self.tag1 = TagFactory.build()
        self.tag2 = TagFactory.build()
        self.update_index()

    def test_positive_feedback_is_saved_with_authenticated_user_and_without_filters(
        self,
    ):
        self.app.set_user(user=self.user)
        params = {"query": self.feedback.search_query}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = self.feedback.remark
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.all()[0]

        self.assertEqual(feedback.search_query, f"query: {self.feedback.search_query}")
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, self.feedback.remark)
        self.assertEqual(feedback.searched_by, self.user)

    def test_negative_feedback_is_saved_with_authenticated_user_and_without_filters(
        self,
    ):
        self.app.set_user(user=self.user)
        params = {"query": self.feedback.search_query}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = self.feedback.remark
        feedback_form["positive"] = "false"
        feedback_form.submit()

        feedback = Feedback.objects.all()[0]

        self.assertEqual(feedback.search_query, f"query: {self.feedback.search_query}")
        self.assertEqual(feedback.search_url, url)
        self.assertFalse(feedback.positive)
        self.assertEqual(feedback.remark, self.feedback.remark)
        self.assertEqual(feedback.searched_by, self.user)

    def test_positive_feedback_is_saved_with_unauthenticated_user_and_without_filters(
        self,
    ):
        params = {"query": self.feedback.search_query}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = self.feedback.remark
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.all()[0]

        self.assertEqual(feedback.search_query, f"query: {self.feedback.search_query}")
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, self.feedback.remark)
        self.assertIsNone(feedback.searched_by)

    def test_negative_feedback_is_saved_with_unauthenticated_user_and_without_filters(
        self,
    ):
        params = {"query": self.feedback.search_query}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = self.feedback.remark
        feedback_form["positive"] = "false"
        feedback_form.submit()

        feedback = Feedback.objects.all()[0]

        self.assertEqual(feedback.search_query, f"query: {self.feedback.search_query}")
        self.assertEqual(feedback.search_url, url)
        self.assertFalse(feedback.positive)
        self.assertEqual(feedback.remark, self.feedback.remark)
        self.assertIsNone(feedback.searched_by)

    def test_positive_feedback_is_saved_with_authenticated_user_and_with_filters(self):
        self.app.set_user(user=self.user)
        params = {
            "query": [self.feedback.search_query],
            "categories": [self.category1.name, self.category2.name],
            "tags": [self.tag1.name, self.tag2.name],
        }
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = self.feedback.remark
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.all()[0]

        self.assertEqual(
            feedback.search_query,
            f"query: {self.feedback.search_query} | categories: {self.category1.name}, {self.category2.name} | tags: {self.tag1.name}, {self.tag2.name}",
        )
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, self.feedback.remark)
        self.assertEqual(feedback.searched_by, self.user)

    def test_positive_feedback_is_saved_with_unauthenticated_user_and_with_filters(
        self,
    ):
        params = {"query": self.feedback.search_query}
        url = f"{reverse('search:search')}?{urllib.parse.urlencode(params, doseq=True)}"
        response = self.app.get(url)

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = self.feedback.remark
        feedback_form["positive"] = "true"
        feedback_form.submit()

        feedback = Feedback.objects.all()[0]

        self.assertEqual(feedback.search_query, f"query: {self.feedback.search_query}")
        self.assertEqual(feedback.search_url, url)
        self.assertTrue(feedback.positive)
        self.assertEqual(feedback.remark, self.feedback.remark)
        self.assertIsNone(feedback.searched_by)

    def test_feedback_form_not_displayed_after_submit(self):
        params = {"query": self.feedback.search_query}
        url = furl(reverse("search:search")).add(params).url
        response = self.app.get(url)

        self.assertIsNotNone(response.html.find(id="feedback_form"))
        self.assertEqual(list(response.context["messages"]), [])

        feedback_form = response.forms["feedback_form"]
        feedback_form["remark"] = self.feedback.remark
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
