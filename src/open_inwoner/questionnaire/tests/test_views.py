from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic import FormView

from django_webtest import WebTest

from ...accounts.tests.factories import UserFactory
from ...pdc.models import Product
from ...pdc.tests.factories import ProductFactory
from ..forms import QuestionnaireStepForm
from ..models import QuestionnaireStep
from ..views import QUESTIONNAIRE_SESSION_KEY, QuestionnaireStepView
from .factories import QuestionnaireStepFactory, QuestionnaireStepFileFactory


class QuestionnaireResetViewTestCase(WebTest):
    def test_clears_session(self):
        path = reverse("questionnaire:reset")
        self.app.get(path)
        self.assertIsNone(self.app.session[QUESTIONNAIRE_SESSION_KEY])

    def test_authenticated_user_redirects(self):
        user = UserFactory()
        path = reverse("questionnaire:reset")
        response = self.app.get(path, user=user)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("accounts:my_profile"), response.url)

    def test_anonymous_user_redirects(self):
        path = reverse("questionnaire:reset")
        response = self.app.get(path)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("root"), response.url)


class QuestionnaireStepViewTestCase(TestCase):
    def test_root_step_404(self):
        path = reverse("questionnaire:root_step", kwargs={"slug": "doesnotexist"})
        self.assertEqual(path, "/questionnaire/doesnotexist")
        response = self.client.get(path)
        self.assertEqual(404, response.status_code)

    def test_root_step_200(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        path = reverse("questionnaire:root_step", kwargs={"slug": "foo"})
        self.assertEqual(path, "/questionnaire/foo")
        response = self.client.get(path)
        self.assertEqual(200, response.status_code)
        self.assertEqual(root, response.context["form"].instance)

    def test_descendent_step_404(self):
        path = reverse(
            "questionnaire:descendent_step",
            kwargs={"root_slug": "doesnotexist", "slug": "doesnotexist"},
        )
        self.assertEqual(path, "/questionnaire/doesnotexist/doesnotexist")
        response = self.client.get(path)
        self.assertEqual(404, response.status_code)

    def test_descendent_step_200(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        descendent = root.add_child(slug="bar")
        path = reverse(
            "questionnaire:descendent_step", kwargs={"root_slug": "foo", "slug": "bar"}
        )
        self.assertEqual(path, "/questionnaire/foo/bar")
        response = self.client.get(path)
        self.assertEqual(200, response.status_code)
        self.assertEqual(descendent, response.context["form"].instance)

    @patch(
        "open_inwoner.questionnaire.models.QuestionnaireStep.get_title",
        new_callable=lambda: "foo",
    )
    def test_render_get_title(self, mock):
        QuestionnaireStepFactory.create(slug="bar")
        path = reverse("questionnaire:root_step", kwargs={"slug": "bar"})
        response = self.client.get(path)
        self.assertContains(response, "foo")

    @patch(
        "open_inwoner.questionnaire.models.QuestionnaireStep.get_description",
        new_callable=lambda: "foo",
    )
    def test_render_get_description(self, mock):
        QuestionnaireStepFactory.create(slug="bar")
        path = reverse("questionnaire:root_step", kwargs={"slug": "bar"})
        response = self.client.get(path)
        self.assertContains(response, "foo")

    def test_render_question(self):
        QuestionnaireStepFactory.create(slug="bar", question="foo")
        path = reverse("questionnaire:root_step", kwargs={"slug": "bar"})
        response = self.client.get(path)
        self.assertContains(response, "foo")

    def test_render_help_text(self):
        QuestionnaireStepFactory.create(slug="bar", help_text="foo")
        path = reverse("questionnaire:root_step", kwargs={"slug": "bar"})
        response = self.client.get(path)
        self.assertContains(response, "foo")

    def test_render_answers(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        root.add_child(parent_answer="bar")
        path = reverse("questionnaire:root_step", kwargs={"slug": "foo"})
        response = self.client.get(path)
        self.assertContains(response, "bar")

    def test_render_content(self):
        QuestionnaireStepFactory.create(slug="bar", content="foo")
        path = reverse("questionnaire:root_step", kwargs={"slug": "bar"})
        response = self.client.get(path)
        self.assertContains(response, "foo")

    def test_render_file(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        QuestionnaireStepFileFactory.create(questionnaire_step=root)
        path = reverse("questionnaire:root_step", kwargs={"slug": "foo"})
        response = self.client.get(path)
        self.assertIn('<aside class="file">', str(response.content))

    def test_render_products(self):
        ProductFactory.create(name="fooz")
        ProductFactory.create(name="barz")
        root = QuestionnaireStepFactory.create(slug="foo")
        root.related_products.set(Product.objects.all())
        path = reverse("questionnaire:root_step", kwargs={"slug": "foo"})
        response = self.client.get(path)
        self.assertContains(response, "fooz")
        self.assertContains(response, "barz")

    def test_render_previous(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        parent = root.add_child(slug="baz")
        parent.add_child(slug="bar")
        path = reverse(
            "questionnaire:descendent_step", kwargs={"root_slug": "foo", "slug": "baz"}
        )
        response = self.client.get(path)
        self.assertContains(response, root.get_absolute_url())

    def test_render_profile(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        root.add_child(slug="bar")
        path = reverse(
            "questionnaire:descendent_step", kwargs={"root_slug": "foo", "slug": "bar"}
        )
        response = self.client.get(path)
        self.assertContains(response, reverse("accounts:my_profile"))

    def test_form_view(self):
        view = QuestionnaireStepView()
        self.assertIsInstance(view, FormView)

    def test_get_object_slug(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        descendent = root.add_child(slug="bar")
        request = RequestFactory().get("/questionnaire/bar")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        view = QuestionnaireStepView()
        view.setup(request, slug="bar")
        object = view.get_object()
        self.assertEqual(object, descendent)

    def test_get_object_slug_404(self):
        QuestionnaireStepFactory.create(slug="foo")
        request = RequestFactory().get("/questionnaire/bar")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        view = QuestionnaireStepView()
        view.setup(request, slug="bar")

        with self.assertRaises(Http404):
            view.get_object()

    def test_get_object_session(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        descendent = root.add_child(slug="bar")
        request = RequestFactory().get("/zelfdiagnose")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        view = QuestionnaireStepView()
        view.setup(request)
        request.session[QUESTIONNAIRE_SESSION_KEY] = "bar"
        object = view.get_object()
        self.assertEqual(object, descendent)

    def test_get_object_session_404(self):
        QuestionnaireStepFactory.create(slug="foo")
        request = RequestFactory().get("/zelfdiagnose")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        view = QuestionnaireStepView()
        view.setup(request)
        request.session[QUESTIONNAIRE_SESSION_KEY] = "bar"

        with self.assertRaises(Http404):
            view.get_object()

    @patch(
        "open_inwoner.questionnaire.views.QuestionnaireStepView.get_object",
        return_value=QuestionnaireStep(slug="foo"),
    )
    def test_get_form_kwargs_get_object(self, mock):
        request = RequestFactory().get("/zelfdiagnose")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        view = QuestionnaireStepView()
        view.setup(request)
        form_kwargs = view.get_form_kwargs()
        self.assertTrue(mock.called)
        self.assertEqual("foo", form_kwargs["instance"].slug)

    @patch(
        "open_inwoner.questionnaire.views.QuestionnaireStepView.get_object",
        return_value=QuestionnaireStep(slug="foo"),
    )
    def test_get_form_kwargs(self, mock):
        request = RequestFactory().get("/zelfdiagnose")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        view = QuestionnaireStepView()
        view.setup(request)
        form_kwargs = view.get_form_kwargs()
        self.assertTrue(mock.called)
        self.assertEqual("foo", form_kwargs["instance"].slug)

    def test_form_valid_valid(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        descendent = root.add_child(slug="bar")
        request = RequestFactory().get("/zelfdiagnose")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        view = QuestionnaireStepView()
        view.setup(request)
        form = QuestionnaireStepForm(instance=root, data={"answer": descendent.pk})
        form.is_valid()
        response = view.form_valid(form)
        self.assertEqual(302, response.status_code)
        self.assertEqual(response.url, descendent.get_absolute_url())


class QuestionnaireStepListViewTestCase(WebTest):
    def setUp(self):
        self.user = UserFactory()

    def test_render_root_nodes_when_user_is_logged_in(self):
        questionnaire = QuestionnaireStepFactory(slug="foo")
        path = reverse("questionnaire:questionnaire_list")
        response = self.app.get(path, user=self.user)
        self.assertTrue(
            response.context["root_nodes"].filter(slug=questionnaire.slug).exists()
        )
        self.assertContains(response, questionnaire.slug)

    def test_render_root_nodes_when_user_is_anonymous(self):
        questionnaire = QuestionnaireStepFactory(slug="foo")
        path = reverse("questionnaire:questionnaire_list")
        response = self.app.get(path)
        self.assertTrue(
            response.context["root_nodes"].filter(slug=questionnaire.slug).exists()
        )
        self.assertContains(response, questionnaire.slug)

    def test_zelfdiagnose_button_is_shown_when_there_are_questionnaires(self):
        QuestionnaireStepFactory()
        path = reverse("accounts:my_profile")
        response = self.app.get(path, user=self.user)
        self.assertContains(response, "Start zelfdiagnose")

    def test_zelfdiagnose_button_is_not_shown_when_there_are_no_questionnaires(self):
        path = reverse("accounts:my_profile")
        response = self.app.get(path, user=self.user)
        self.assertNotContains(response, "Start zelfdiagnose")
