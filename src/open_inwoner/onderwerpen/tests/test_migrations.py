from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import tag

from filer.models import Image

from open_inwoner.utils.test import temp_media_root
from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class QuestionAnswerMigrationTest(TestSuccessfulMigrations):
    """Tests the migration of Question answer field to ProsemirrorModelField."""

    migrate_from = "0066_category_access_groups"
    migrate_to = "0067_question_answer"
    app = "pdc"

    def setUpBeforeMigration(self, apps):
        Question = apps.get_model("pdc", "Question")
        Category = apps.get_model("pdc", "Category")
        Product = apps.get_model("pdc", "Product")

        category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            published=True,
            path="0001",
            depth=1,
            numchild=0,
        )
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            published=True,
        )

        self.question_with_bold = Question.objects.create(
            category=category,
            question="Test question with bold",
            answer="**Bold text** in answer",
            order=0,
        )

        self.question_with_italic = Question.objects.create(
            category=category,
            question="Test question with italic",
            answer="_Italic text_ in answer",
            order=1,
        )

        self.question_with_link = Question.objects.create(
            category=category,
            question="Test question with link",
            answer="Check [this link](https://example.com) for more info",
            order=2,
        )

        self.question_with_mixed_formatting = Question.objects.create(
            category=category,
            question="Test question with mixed formatting",
            answer="**Bold text** and _italic text_ with a [link](https://example.com)",
            order=3,
        )

        self.question_with_empty_answer = Question.objects.create(
            category=category,
            question="Test question with empty answer",
            answer="",
            order=4,
        )

        self.question_with_whitespace_answer = Question.objects.create(
            category=category,
            question="Test question with whitespace answer",
            answer="   ",
            order=5,
        )

        self.question_with_plain_text = Question.objects.create(
            product=product,
            question="Test question with plain text",
            answer="Plain text without any formatting",
            order=0,
        )

        self.question_with_quoted_answer = Question.objects.create(
            category=category,
            question="Test question with quoted answer",
            answer='"Quoted answer text"',
            order=6,
        )

    def test_bold_text_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_bold.id)

        expected_html = "<p><strong>Bold text</strong> in answer</p>"
        self.assertEqual(question.answer.html, expected_html)

    def test_italic_text_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_italic.id)

        expected_html = "<p><em>Italic text</em> in answer</p>"
        self.assertEqual(question.answer.html, expected_html)

    def test_link_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_link.id)

        expected_html = (
            '<p>Check <a href="https://example.com">this link</a> for more info</p>'
        )
        self.assertEqual(question.answer.html, expected_html)

    def test_mixed_formatting_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_mixed_formatting.id)

        expected_html = '<p><strong>Bold text</strong> and <em>italic text</em> with a <a href="https://example.com">link</a></p>'
        self.assertEqual(question.answer.html, expected_html)

    def test_empty_answer_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_empty_answer.id)

        self.assertIsNotNone(question.answer)
        self.assertEqual(question.answer.html, "")

    def test_whitespace_answer_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_whitespace_answer.id)

        self.assertIsNotNone(question.answer)
        self.assertEqual(question.answer.html, "")

    def test_plain_text_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_plain_text.id)

        expected_html = "<p>Plain text without any formatting</p>"
        self.assertEqual(question.answer.html, expected_html)

    def test_quoted_answer_migration(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.get(id=self.question_with_quoted_answer.id)

        expected_html = "<p>Quoted answer text</p>"
        self.assertEqual(question.answer.html, expected_html)

    def test_temporary_field_removed(self):
        Question = self.apps.get_model("pdc", "Question")
        question = Question.objects.first()

        self.assertFalse(hasattr(question, "answer_tmp"))


@tag("migrations")
class CategoryDescriptionMigrationTest(TestSuccessfulMigrations):
    """Tests the migration of Category description field to ProsemirrorModelField."""

    migrate_from = "0067_question_answer"
    migrate_to = "0070_category_description_schema_2"
    app = "pdc"

    def setUp(self):
        with temp_media_root():
            super().setUp()

    def setUpBeforeMigration(self, apps):
        Category = apps.get_model("pdc", "Category")

        # Create test images (using current Image model, not historical)
        self.image1 = Image(
            file=SimpleUploadedFile(
                "test_image_1.png", b"fake image 1", content_type="image/png"
            ),
            original_filename="test_image_1.png",
        )
        self.image1.save()

        self.image2 = Image(
            file=SimpleUploadedFile(
                "test_image_2.png", b"fake image 2", content_type="image/png"
            ),
            original_filename="test_image_2.png",
        )
        self.image2.save()

        # Get the image URLs
        self.image1_url = self.image1.url
        self.image2_url = self.image2.url

        # Categories with various markdown content
        self.category_with_bold = Category.objects.create(
            name="Category with Bold",
            slug="category-bold",
            published=True,
            path="0001",
            depth=1,
            numchild=0,
            description="**Bold text** in description",
        )

        self.category_with_italic = Category.objects.create(
            name="Category with Italic",
            slug="category-italic",
            published=True,
            path="0002",
            depth=1,
            numchild=0,
            description="_Italic text_ in description",
        )

        self.category_with_link = Category.objects.create(
            name="Category with Link",
            slug="category-link",
            published=True,
            path="0003",
            depth=1,
            numchild=0,
            description="Check [this link](https://example.com) for more info",
        )

        self.category_with_image = Category.objects.create(
            name="Category with Image",
            slug="category-image",
            published=True,
            path="0004",
            depth=1,
            numchild=0,
            description=f"Text before image ![Alt text]({self.image1_url}) text after image",
        )

        self.category_with_image_and_formatting = Category.objects.create(
            name="Category with Image and Formatting",
            slug="category-image-formatting",
            published=True,
            path="0005",
            depth=1,
            numchild=0,
            description=f"**Bold text** before image ![Test image]({self.image1_url}) and _italic_ after",
        )

        self.category_with_multiple_images = Category.objects.create(
            name="Category with Multiple Images",
            slug="category-multiple-images",
            published=True,
            path="0006",
            depth=1,
            numchild=0,
            description=f"First image: ![Image 1]({self.image1_url}), second image: ![Image 2]({self.image2_url})",
        )

        self.category_with_empty_description = Category.objects.create(
            name="Category with Empty Description",
            slug="category-empty",
            published=True,
            path="0007",
            depth=1,
            numchild=0,
            description="",
        )

        self.category_with_whitespace_description = Category.objects.create(
            name="Category with Whitespace Description",
            slug="category-whitespace",
            published=True,
            path="0008",
            depth=1,
            numchild=0,
            description="   ",
        )

        self.category_with_plain_text = Category.objects.create(
            name="Category with Plain Text",
            slug="category-plain",
            published=True,
            path="0009",
            depth=1,
            numchild=0,
            description="Plain text without any formatting",
        )

    def test_bold_text_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_bold.id)

        expected_html = "<p><strong>Bold text</strong> in description</p>"
        self.assertEqual(category.description.html, expected_html)

    def test_italic_text_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_italic.id)

        expected_html = "<p><em>Italic text</em> in description</p>"
        self.assertEqual(category.description.html, expected_html)

    def test_link_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_link.id)

        expected_html = (
            '<p>Check <a href="https://example.com">this link</a> for more info</p>'
        )
        self.assertEqual(category.description.html, expected_html)

    def test_image_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_image.id)

        # Check that image is in the description
        self.assertIn("filer_image", str(category.description.doc))

        # Check that imageId is set correctly
        doc = category.description.doc
        image_node = None
        for node in doc.get("content", []):
            for content_item in node.get("content", []):
                if content_item.get("type") == "filer_image":
                    image_node = content_item
                    break
            if image_node:
                break

        self.assertIsNotNone(image_node, "Image node not found in document")
        self.assertEqual(image_node["attrs"]["imageId"], str(self.image1.id))
        self.assertEqual(image_node["attrs"]["alt"], "Alt text")

    def test_image_with_formatting_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_image_and_formatting.id)

        # Check that both formatting and image are present
        html = category.description.html
        self.assertIn("<strong>Bold text</strong>", html)
        self.assertIn("<em>italic</em>", html)
        self.assertIn("filer_image", str(category.description.doc))

    def test_multiple_images_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_multiple_images.id)

        # Check that both images are in the document
        doc = category.description.doc
        image_nodes = []
        for node in doc.get("content", []):
            image_nodes.extend(
                content_item
                for content_item in node.get("content", [])
                if content_item.get("type") == "filer_image"
            )

        self.assertEqual(len(image_nodes), 2, "Expected 2 images in document")
        self.assertEqual(image_nodes[0]["attrs"]["imageId"], str(self.image1.id))
        self.assertEqual(image_nodes[1]["attrs"]["imageId"], str(self.image2.id))

    def test_empty_description_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_empty_description.id)

        self.assertIsNotNone(category.description)
        self.assertEqual(category.description.html, "")

    def test_whitespace_description_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_whitespace_description.id)

        self.assertIsNotNone(category.description)
        self.assertEqual(category.description.html, "")

    def test_plain_text_migration(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.get(id=self.category_with_plain_text.id)

        expected_html = "<p>Plain text without any formatting</p>"
        self.assertEqual(category.description.html, expected_html)

    def test_temporary_field_removed(self):
        Category = self.apps.get_model("pdc", "Category")
        category = Category.objects.first()

        self.assertFalse(hasattr(category, "description_tmp"))


@tag("migrations")
class ProductContentMigrationTest(TestSuccessfulMigrations):
    """Tests the migration of Product content field to ProsemirrorModelField."""

    migrate_from = "0070_category_description_schema_2"
    migrate_to = "0073_product_content_schema_2"
    app = "pdc"

    def setUp(self):
        with temp_media_root():
            super().setUp()

    def setUpBeforeMigration(self, apps):
        Product = apps.get_model("pdc", "Product")

        # Create test images (using current Image model, not historical)
        self.image1 = Image(
            file=SimpleUploadedFile(
                "test_product_image_1.png", b"fake image 1", content_type="image/png"
            ),
            original_filename="test_product_image_1.png",
        )
        self.image1.save()

        self.image2 = Image(
            file=SimpleUploadedFile(
                "test_product_image_2.png", b"fake image 2", content_type="image/png"
            ),
            original_filename="test_product_image_2.png",
        )
        self.image2.save()

        # Get the image URLs
        self.image1_url = self.image1.url
        self.image2_url = self.image2.url

        # Products with various markdown content
        self.product_with_bold = Product.objects.create(
            name="Product with Bold",
            slug="product-bold",
            published=True,
            content="**Bold text** in content",
        )

        self.product_with_italic = Product.objects.create(
            name="Product with Italic",
            slug="product-italic",
            published=True,
            content="_Italic text_ in content",
        )

        self.product_with_link = Product.objects.create(
            name="Product with Link",
            slug="product-link",
            published=True,
            content="Check [this link](https://example.com) for more info",
        )

        self.product_with_image = Product.objects.create(
            name="Product with Image",
            slug="product-image",
            published=True,
            content=f"Text before image ![Alt text]({self.image1_url}) text after image",
        )

        self.product_with_image_and_formatting = Product.objects.create(
            name="Product with Image and Formatting",
            slug="product-image-formatting",
            published=True,
            content=f"**Bold text** before image ![Test image]({self.image1_url}) and _italic_ after",
        )

        self.product_with_multiple_images = Product.objects.create(
            name="Product with Multiple Images",
            slug="product-multiple-images",
            published=True,
            content=f"First image: ![Image 1]({self.image1_url}), second image: ![Image 2]({self.image2_url})",
        )

        self.product_with_empty_content = Product.objects.create(
            name="Product with Empty Content",
            slug="product-empty",
            published=True,
            content="",
        )

        self.product_with_whitespace_content = Product.objects.create(
            name="Product with Whitespace Content",
            slug="product-whitespace",
            published=True,
            content="   ",
        )

        self.product_with_plain_text = Product.objects.create(
            name="Product with Plain Text",
            slug="product-plain",
            published=True,
            content="Plain text without any formatting",
        )

    def test_bold_text_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_bold.id)

        expected_html = "<p><strong>Bold text</strong> in content</p>"
        self.assertEqual(product.content.html, expected_html)

    def test_italic_text_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_italic.id)

        expected_html = "<p><em>Italic text</em> in content</p>"
        self.assertEqual(product.content.html, expected_html)

    def test_link_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_link.id)

        expected_html = (
            '<p>Check <a href="https://example.com">this link</a> for more info</p>'
        )
        self.assertEqual(product.content.html, expected_html)

    def test_image_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_image.id)

        # Check that image is in the content
        self.assertIn("filer_image", str(product.content.doc))

        # Check that imageId is set correctly
        doc = product.content.doc
        image_node = None
        for node in doc.get("content", []):
            for content_item in node.get("content", []):
                if content_item.get("type") == "filer_image":
                    image_node = content_item
                    break
            if image_node:
                break

        self.assertIsNotNone(image_node, "Image node not found in document")
        self.assertEqual(image_node["attrs"]["imageId"], str(self.image1.id))
        self.assertEqual(image_node["attrs"]["alt"], "Alt text")

    def test_image_with_formatting_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_image_and_formatting.id)

        # Check that both formatting and image are present
        html = product.content.html
        self.assertIn("<strong>Bold text</strong>", html)
        self.assertIn("<em>italic</em>", html)
        self.assertIn("filer_image", str(product.content.doc))

    def test_multiple_images_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_multiple_images.id)

        # Check that both images are in the document
        doc = product.content.doc
        image_nodes = []
        for node in doc.get("content", []):
            image_nodes.extend(
                content_item
                for content_item in node.get("content", [])
                if content_item.get("type") == "filer_image"
            )

        self.assertEqual(len(image_nodes), 2, "Expected 2 images in document")
        self.assertEqual(image_nodes[0]["attrs"]["imageId"], str(self.image1.id))
        self.assertEqual(image_nodes[1]["attrs"]["imageId"], str(self.image2.id))

    def test_empty_content_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_empty_content.id)

        self.assertIsNotNone(product.content)
        self.assertEqual(product.content.html, "")

    def test_whitespace_content_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_whitespace_content.id)

        self.assertIsNotNone(product.content)
        self.assertEqual(product.content.html, "")

    def test_plain_text_migration(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.get(id=self.product_with_plain_text.id)

        expected_html = "<p>Plain text without any formatting</p>"
        self.assertEqual(product.content.html, expected_html)

    def test_temporary_field_removed(self):
        Product = self.apps.get_model("pdc", "Product")
        product = Product.objects.first()

        self.assertFalse(hasattr(product, "content_tmp"))
