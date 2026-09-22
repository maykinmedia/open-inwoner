from django.test import tag

from open_inwoner.pdc.tests.factories import CategoryFactory, ProductFactory
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


def _text_with_link(text, href):
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "marks": [{"type": "link", "attrs": {"href": href}}],
                    }
                ],
            }
        ],
    }


def _table_with_link(text, href):
    return {
        "type": "doc",
        "content": [
            {
                "type": "table",
                "content": [
                    {
                        "type": "table_row",
                        "content": [
                            {
                                "type": "table_cell",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": text,
                                                "marks": [
                                                    {
                                                        "type": "link",
                                                        "attrs": {"href": href},
                                                    }
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


@tag("migrations")
class SanitizeProsemirrorLinkHrefsMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0078: strip unsafe hrefs from stored prosemirror link marks
    on Category.description, Product.content and Question.answer.
    """

    migrate_from = "0077_alter_question_answer"
    migrate_to = "0078_sanitize_prosemirror_link_hrefs"
    app = "pdc"

    def setUpBeforeMigration(self, apps):
        Category = apps.get_model("pdc", "Category")
        Product = apps.get_model("pdc", "Product")
        Question = apps.get_model("pdc", "Question")

        real_category = CategoryFactory()
        category = Category.objects.get(id=real_category.id)
        Category.objects.filter(pk=category.pk).update(
            description=_text_with_link("click", "javascript:alert(1)")
        )
        self.category = category

        real_safe_category = CategoryFactory()
        safe_category = Category.objects.get(id=real_safe_category.id)
        Category.objects.filter(pk=safe_category.pk).update(
            description=_text_with_link("click", "https://example.com")
        )
        self.safe_category = safe_category

        real_product = ProductFactory(categories=[real_category])
        product = Product.objects.get(id=real_product.id)
        Product.objects.filter(pk=product.pk).update(
            content=_table_with_link("click", "javascript:alert(document.cookie)")
        )
        self.product = product

        self.empty_question = Question.objects.create(
            category=category,
            question="Empty answer?",
            answer=None,
            order=0,
        )

    def _get_category(self, category):
        Category = self.apps.get_model("pdc", "Category")
        return Category.objects.get(id=category.id)

    def _get_product(self, product):
        Product = self.apps.get_model("pdc", "Product")
        return Product.objects.get(id=product.id)

    def _get_question(self, question):
        Question = self.apps.get_model("pdc", "Question")
        return Question.objects.get(id=question.id)

    def test_unsafe_href_stripped_from_category_description(self):
        category = self._get_category(self.category)
        text_node = category.description.raw_data["content"][0]["content"][0]
        self.assertEqual(text_node["marks"], [])
        self.assertEqual(text_node["text"], "click")

    def test_safe_href_preserved_on_category_description(self):
        category = self._get_category(self.safe_category)
        text_node = category.description.raw_data["content"][0]["content"][0]
        self.assertEqual(text_node["marks"][0]["attrs"]["href"], "https://example.com")

    def test_unsafe_href_stripped_from_nested_product_content(self):
        product = self._get_product(self.product)
        text_node = product.content.raw_data["content"][0]["content"][0]["content"][0][
            "content"
        ][0]["content"][0]
        self.assertEqual(text_node["marks"], [])
        self.assertEqual(text_node["text"], "click")

    def test_empty_question_answer_is_untouched(self):
        question = self._get_question(self.empty_question)
        self.assertIsNone(question.answer.raw_data)
