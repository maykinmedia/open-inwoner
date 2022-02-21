from django.test import TestCase

from ..forms import QuestionnaireStepChoiceField, QuestionnaireStepForm
from .factories import QuestionnaireStepFactory


class QuestionnaireStepChoiceFieldTestCase(TestCase):
    def test_label_from_instance(self):
        root = QuestionnaireStepFactory.create(question="foo")
        QuestionnaireStepFactory.create(parent=root, parent_answer="bar")
        field = QuestionnaireStepChoiceField(queryset=root.get_children())

        for (index, choice) in enumerate(field.choices):
            if index == 0:
                continue
            self.assertEqual("bar", choice[1])


class QuestionnaireStepFormTestCase(TestCase):
    def test_answer(self):
        root = QuestionnaireStepFactory.create()
        QuestionnaireStepFactory.create(parent=root)
        form = QuestionnaireStepForm(instance=root)
        self.assertIn("answer", form.fields)

    def test_no_answer(self):
        root = QuestionnaireStepFactory.create()
        form = QuestionnaireStepForm(instance=root)
        self.assertNotIn("answer", form.fields)
