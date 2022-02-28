from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext as _

from .factories import QuestionnaireStepFactory, QuestionnaireStepFileFactory
from ..models import QuestionnaireStep


class QuestionnaireStepTestCase(TestCase):
    def test_create(self):
        QuestionnaireStepFactory.create()

    def test_slug_unique(self):
        with self.assertRaises(IntegrityError):
            QuestionnaireStepFactory.create(slug="foo")
            QuestionnaireStepFactory.create(slug="foo")

    def test_str(self):
        root = QuestionnaireStepFactory.create(question="foo")
        self.assertEqual("foo", str(root))

    def test_get_absolute_url_root(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        self.assertEqual("/zelfdiagnose/foo", root.get_absolute_url())

    def test_get_absolute_url_descendent(self):
        root = QuestionnaireStepFactory.create(slug="foo")
        descendent = root.add_child(slug="bar")
        self.assertEqual("/zelfdiagnose/foo/bar", descendent.get_absolute_url())

    def test_get_title_root(self):
        root = QuestionnaireStepFactory.create(slug="foo", title="foo")
        self.assertEqual("foo", root.get_title())

    def test_get_title_descendent_self(self):
        root = QuestionnaireStepFactory.create(slug="foo", title="foo")
        descendent = root.add_child(slug="bar", title="bar")
        self.assertEqual("bar", descendent.get_title())

    def test_get_title_descendent_inherited(self):
        root = QuestionnaireStepFactory.create(slug="foo", title="foo")
        parent = root.add_child(slug="baz", title="baz")
        descendent = parent.add_child(slug="bar")
        self.assertEqual("foo", descendent.get_title())

    def test_get_description_root(self):
        root = QuestionnaireStepFactory.create(slug="foo", description="foo")
        self.assertEqual("foo", root.get_description())

    def test_get_description_descendent_self(self):
        root = QuestionnaireStepFactory.create(slug="foo", description="foo")
        descendent = root.add_child(slug="bar", description="bar")
        self.assertEqual("bar", descendent.get_description())

    def test_get_description_descendent_inherited(self):
        root = QuestionnaireStepFactory.create(slug="foo", description="foo")
        parent = root.add_child(slug="baz", description="baz")
        descendent = parent.add_child()
        self.assertEqual("foo", descendent.get_description())

    def test_get_max_descendant_depth(self):
        root = QuestionnaireStep.add_root(slug="foo")
        parent_1 = root.add_child(slug="baz_1")
        descendant_1 = parent_1.add_child(slug="bar_1")
        parent_2 = root.add_child(slug="baz_2")
        parent_3 = parent_2.add_child(slug="baz_3")
        descendant_2 = parent_3.add_child(slug="bar_2")

        self.assertEqual(4, root.get_max_descendant_depth())
        self.assertEqual(4, descendant_2.get_max_descendant_depth())
        self.assertEqual(3, parent_1.get_max_descendant_depth())
        self.assertEqual(3, descendant_1.get_max_descendant_depth())

class QuestionnaireStepFileTestCase(TestCase):
    def test_create(self):
        QuestionnaireStepFileFactory.create()

    def test_str(self):
        questionnaire_step_file = QuestionnaireStepFileFactory.create()
        self.assertEqual(_("Geen bestand geselecteerd."), str(questionnaire_step_file))
