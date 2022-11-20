from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext as _

from ..models import QuestionnaireStep
from .factories import QuestionnaireStepFactory, QuestionnaireStepFileFactory


class QuestionnaireStepTestCase(TestCase):
    def test_create(self):
        QuestionnaireStepFactory.create()

    def test_multiple_root(self):
        root_1 = QuestionnaireStep.add_root(code="foo", slug="foo")
        root_2 = QuestionnaireStep.add_root(code="fooz", slug="fooz")
        self.assertIsNone(root_1.get_parent())
        self.assertIsNone(root_2.get_parent())

    def test_slug_unique(self):
        with self.assertRaises(IntegrityError):
            QuestionnaireStepFactory.create(code="foo", slug="foo")
            QuestionnaireStepFactory.create(code="foo", slug="foo")

    def test_str(self):
        root = QuestionnaireStepFactory.create(question="foo")
        self.assertTrue("foo" in str(root))

    def test_get_absolute_url_root(self):
        root = QuestionnaireStepFactory.create(code="foo", slug="foo")
        self.assertEqual("/questionnaire/foo", root.get_absolute_url())

    def test_get_absolute_url_descendent(self):
        root = QuestionnaireStepFactory.create(code="foo", slug="foo")
        descendent = root.add_child(code="bar", slug="bar")
        self.assertEqual("/questionnaire/foo/bar", descendent.get_absolute_url())

    def test_get_title_root(self):
        root = QuestionnaireStepFactory.create(code="foo", slug="foo", title="foo")
        self.assertEqual("foo", root.get_title())

    def test_get_title_descendent_self(self):
        root = QuestionnaireStepFactory.create(code="foo", slug="foo", title="foo")
        descendent = root.add_child(code="bar", slug="bar", title="bar")
        self.assertEqual("bar", descendent.get_title())

    def test_get_title_descendent_inherited(self):
        root = QuestionnaireStepFactory.create(code="foo", slug="foo", title="foo")
        parent = root.add_child(code="baz", slug="baz", title="baz")
        descendent = parent.add_child(code="bar", slug="bar")
        self.assertEqual("foo", descendent.get_title())

    def test_get_description_root(self):
        root = QuestionnaireStepFactory.create(
            code="foo", slug="foo", description="foo"
        )
        self.assertEqual("foo", root.get_description())

    def test_get_description_descendent_self(self):
        root = QuestionnaireStepFactory.create(
            code="foo", slug="foo", description="foo"
        )
        descendent = root.add_child(code="bar", slug="bar", description="bar")
        self.assertEqual("bar", descendent.get_description())

    def test_get_description_descendent_inherited(self):
        root = QuestionnaireStepFactory.create(
            code="foo", slug="foo", description="foo"
        )
        parent = root.add_child(code="baz", slug="baz", description="baz")
        descendent = parent.add_child()
        self.assertEqual("foo", descendent.get_description())

    def test_get_max_descendant_depth(self):
        root = QuestionnaireStep.add_root(code="foo", slug="foo")
        parent_1 = root.add_child(code="baz_1", slug="baz_1")
        descendant_1 = parent_1.add_child(code="bar_1", slug="bar_1")
        parent_2 = root.add_child(code="baz_2", slug="baz_2")
        parent_3 = parent_2.add_child(code="baz_3", slug="baz_3")
        descendant_2 = parent_3.add_child(code="bar_2", slug="bar_2")

        self.assertEqual(4, root.get_max_descendant_depth())
        self.assertEqual(4, descendant_2.get_max_descendant_depth())
        self.assertEqual(3, parent_1.get_max_descendant_depth())
        self.assertEqual(3, descendant_1.get_max_descendant_depth())

    def test_get_tree_path(self):
        root = QuestionnaireStep.add_root(code="foo", slug="foo")
        parent_1 = root.add_child(code="baz_1", slug="baz_1")
        descendant_1 = parent_1.add_child(code="bar_1", slug="bar_1")
        parent_2 = root.add_child(code="baz_2", slug="baz_2")
        parent_3 = parent_2.add_child(code="baz_3", slug="baz_3")
        descendant_2 = parent_3.add_child(code="bar_2", slug="bar_2")

        path_root = root.get_tree_path()
        self.assertEqual(1, len(path_root))
        self.assertEqual(root, path_root[0])

        path_parent_1 = parent_1.get_tree_path()
        self.assertEqual(2, len(path_parent_1))
        self.assertEqual(root, path_parent_1[0])
        self.assertEqual(parent_1, path_parent_1[1])

        path_descendant_1 = descendant_1.get_tree_path()
        self.assertEqual(3, len(path_descendant_1))
        self.assertEqual(root, path_descendant_1[0])
        self.assertEqual(parent_1, path_descendant_1[1])
        self.assertEqual(descendant_1, path_descendant_1[2])

        path_parent_2 = parent_2.get_tree_path()
        self.assertEqual(2, len(path_parent_2))
        self.assertEqual(root, path_parent_2[0])
        self.assertEqual(parent_2, path_parent_2[1])

        path_parent_3 = parent_3.get_tree_path()
        self.assertEqual(3, len(path_parent_3))
        self.assertEqual(root, path_parent_3[0])
        self.assertEqual(parent_2, path_parent_3[1])
        self.assertEqual(parent_3, path_parent_3[2])

        path_descendant_2 = descendant_2.get_tree_path()
        self.assertEqual(4, len(path_descendant_2))
        self.assertEqual(root, path_descendant_2[0])
        self.assertEqual(parent_2, path_descendant_2[1])
        self.assertEqual(parent_3, path_descendant_2[2])
        self.assertEqual(descendant_2, path_descendant_2[3])


class QuestionnaireStepFileTestCase(TestCase):
    def test_create(self):
        QuestionnaireStepFileFactory.create()

    def test_str(self):
        questionnaire_step_file = QuestionnaireStepFileFactory.create()
        self.assertEqual(_("Geen bestand geselecteerd."), str(questionnaire_step_file))
