from django.test import TestCase
from django.utils.translation import gettext as _


from .factories import QuestionnaireStepFactory, QuestionnaireStepFileFactory


class QuestionnaireStepTestCase(TestCase):
    def test_create(self):
        QuestionnaireStepFactory.create()

    def test_str(self):
        root = QuestionnaireStepFactory.create(question="foo")
        self.assertEqual("foo", str(root))

    def test_get_absolute_url_root(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        self.assertEqual("/zelfdiagnose/foo", root.get_absolute_url())

    def test_get_absolute_url_descendent(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        descendent = QuestionnaireStepFactory.create(parent=root, slug="bar")
        self.assertEqual("/zelfdiagnose/foo/bar", descendent.get_absolute_url())

    def test_get_title_root(self):
        root = QuestionnaireStepFactory.create(title="foo")
        self.assertEqual("foo", root.get_title())

    def test_get_title_descendent_self(self):
        root = QuestionnaireStepFactory.create(title="foo")
        descendent = QuestionnaireStepFactory.create(parent=root, title="bar")
        self.assertEqual("bar", descendent.get_title())

    def test_get_title_descendent_inherited(self):
        root = QuestionnaireStepFactory.create(title="foo")
        parent = QuestionnaireStepFactory.create(parent=root, title="baz")
        descendent = QuestionnaireStepFactory.create(parent=parent)
        self.assertEqual("foo", descendent.get_title())

    def test_get_description_root(self):
        root = QuestionnaireStepFactory.create(description="foo")
        self.assertEqual("foo", root.get_description())

    def test_get_description_descendent_self(self):
        root = QuestionnaireStepFactory.create(description="foo")
        descendent = QuestionnaireStepFactory.create(parent=root, description="bar")
        self.assertEqual("bar", descendent.get_description())

    def test_get_description_descendent_inherited(self):
        root = QuestionnaireStepFactory.create(description="foo")
        parent = QuestionnaireStepFactory.create(parent=root, description="baz")
        descendent = QuestionnaireStepFactory.create(parent=parent)
        self.assertEqual("foo", descendent.get_description())


class QuestionnaireStepFileTestCase(TestCase):
    def test_create(self):
        QuestionnaireStepFileFactory.create()

    def test_str(self):
        questionnaire_step_file = QuestionnaireStepFileFactory.create()
        self.assertEqual(_("Geen bestand geselecteerd."), str(questionnaire_step_file))
