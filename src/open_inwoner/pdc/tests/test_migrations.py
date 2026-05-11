from django.test import tag

from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class QuestionAnswerMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0067: answer (text field) → answer (ProseMirror).

    Scenarios:
    - Markdown content → converted to ProseMirror doc
    - Empty string → answer stays NULL
    - Whitespace-only → answer stays NULL
    """

    migrate_from = "0066_category_access_groups"
    migrate_to = "0067_question_answer"
    app = "pdc"

    def setUpBeforeMigration(self, apps):
        Question = apps.get_model("pdc", "Question")
        Category = apps.get_model("pdc", "Category")

        real_category = CategoryFactory()
        category = Category.objects.get(id=real_category.id)

        self.question_with_content = Question.objects.create(
            category=category,
            question="What is bold?",
            answer="**Bold** answer text",
            order=0,
        )
        self.question_empty = Question.objects.create(
            category=category,
            question="Empty answer?",
            answer="",
            order=1,
        )
        self.question_whitespace = Question.objects.create(
            category=category,
            question="Whitespace answer?",
            answer="   ",
            order=2,
        )

    def _get(self, question):
        Question = self.apps.get_model("pdc", "Question")
        return Question.objects.get(id=question.id)

    def test_markdown_content_is_converted(self):
        question = self._get(self.question_with_content)
        self.assertIsNotNone(question.answer.raw_data)
        self.assertEqual(question.answer.raw_data["type"], "doc")

    def test_empty_content_is_skipped(self):
        question = self._get(self.question_empty)
        self.assertIsNone(question.answer.raw_data)

    def test_whitespace_content_is_skipped(self):
        question = self._get(self.question_whitespace)
        self.assertIsNone(question.answer.raw_data)
