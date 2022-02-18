from django.test import TestCase
from django.urls import reverse

from .factories import QuestionnaireStepFactory


class QuestionnaireStepViewTestCase(TestCase):
    def test_index_404(self):
        path = reverse('questionnaire:index')
        response = self.client.get(path)
        self.assertEqual(404, response.status_code)

    def test_index_200(self):
        root = QuestionnaireStepFactory.create()
        path = reverse('questionnaire:index')
        response = self.client.get(path)
        self.assertEqual(200, response.status_code)
        self.assertEqual(root, response.context["form"].instance)

    def test_root_step_404(self):
        path = reverse('questionnaire:root_step', kwargs={"slug": "doesnotexist"})
        self.assertEqual(path, "/zelfdiagnose/doesnotexist")
        response = self.client.get(path)
        self.assertEqual(404, response.status_code)

    def test_root_step_200(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        path = reverse('questionnaire:root_step', kwargs={"slug": "foo"})
        self.assertEqual(path, "/zelfdiagnose/foo")
        response = self.client.get(path)
        self.assertEqual(200, response.status_code)
        self.assertEqual(root, response.context["form"].instance)

    def test_descendent_step_404(self):
        path = reverse('questionnaire:descendent_step', kwargs={"root_slug": "doesnotexist", "slug": "doesnotexist"})
        self.assertEqual(path, "/zelfdiagnose/doesnotexist/doesnotexist")
        response = self.client.get(path)
        self.assertEqual(404, response.status_code)

    def test_descendent_step_200(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        descendent = QuestionnaireStepFactory.create(parent=root, slug="bar")
        path = reverse('questionnaire:descendent_step', kwargs={"root_slug": "foo", "slug": "bar"})
        self.assertEqual(path, "/zelfdiagnose/foo/bar")
        response = self.client.get(path)
        self.assertEqual(200, response.status_code)
        self.assertEqual(descendent, response.context["form"].instance)
