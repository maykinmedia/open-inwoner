from html import escape
from unittest.mock import patch

from django.test import override_settings, tag
from django.urls import reverse

from django_webtest import WebTest
from playwright.sync_api import expect

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.playwright import PlaywrightSyncLiveServerTestCase

from ...media.tests.factories import VideoFactory
from ..models import CategoryProduct
from .factories import CategoryFactory, ProductFactory, QuestionFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestPublishedProducts(WebTest):
    def test_only_published_products_exist_on_categories_page_when_anonymous(self):
        category = CategoryFactory(path="0001", name="First one", slug="first-one")
        product1 = ProductFactory(categories=(category,))
        product2 = ProductFactory(categories=(category,), published=False)
        response = self.app.get(
            reverse("products:category_detail", kwargs={"slug": category.slug})
        )
        self.assertEqual(list(response.context["products"]), [product1])

    def test_only_published_products_exist_on_categories_page_when_logged_in(self):
        user = UserFactory()
        category = CategoryFactory(path="0001", name="First one", slug="first-one")
        product1 = ProductFactory(categories=(category,))
        product2 = ProductFactory(categories=(category,), published=False)
        response = self.app.get(
            reverse("products:category_detail", kwargs={"slug": category.slug}),
            user=user,
        )
        self.assertEqual(list(response.context["products"]), [product1])

    def test_only_published_related_products_exist_on_product_page_when_anonymous(self):
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        product3 = ProductFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product1.slug})
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_related_products_exist_on_product_page_when_logged_in(self):
        user = UserFactory()
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        product3 = ProductFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product1.slug}),
            user=user,
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_products_exist_on_zelfdiagnose_when_anoynymous(self):
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        questionnaire = QuestionnaireStepFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("products:root_step", kwargs={"slug": questionnaire.slug})
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_products_exist_on_zelfdiagnose_when_logged_in(self):
        user = UserFactory()
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        questionnaire = QuestionnaireStepFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("products:root_step", kwargs={"slug": questionnaire.slug}),
            user=user,
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_products_exist_on_product_finder_page_when_anonymous(self):
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        response = self.app.get(reverse("products:product_finder"))
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 1)
        self.assertIn(product1, possible_products)
        self.assertNotIn(product2, possible_products)

    def test_only_published_products_exist_on_product_finder_page_when_logged_in(self):
        user = UserFactory()
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        response = self.app.get(reverse("products:product_finder"), user=user)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 1)
        self.assertIn(product1, possible_products)
        self.assertNotIn(product2, possible_products)

    def test_products_are_ordered(self):
        category = CategoryFactory(path="0001", name="First one", slug="first-one")
        product1 = ProductFactory(categories=(category,))
        product2 = ProductFactory(categories=(category,))

        response = self.app.get(
            reverse("products:category_detail", kwargs={"slug": category.slug})
        )
        self.assertEqual(list(response.context["products"]), [product1, product2])

        # grab the ordered many-2-many and move ordering
        prodcat = CategoryProduct.objects.get(category=category, product=product1)
        prodcat.down()

        response = self.app.get(
            reverse("products:category_detail", kwargs={"slug": category.slug})
        )
        self.assertEqual(list(response.context["products"]), [product2, product1])

    def test_product_in_nested_category(self):
        # regression test for Taiga #1402
        category1 = CategoryFactory(path="0001", name="First one", slug="first-one")
        category2 = category1.add_child(
            path="0002", name="Second one", slug="second-one"
        )
        # add product to category2 and access it through that (so category1 is a parent)
        product1 = ProductFactory(categories=(category2,))
        response = self.app.get(
            reverse("products:category_detail", kwargs={"slug": category2.slug})
        )
        self.assertEqual(list(response.context["products"]), [product1])


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestProductFAQ(WebTest):
    def test_product_detail_shows_product_faq(self):
        product = ProductFactory()
        question_1 = QuestionFactory(
            question="Does this sort to the bottom?", order=10, product=product
        )
        question_2 = QuestionFactory(
            question="Sorting to the top", order=1, product=product
        )

        other_product = ProductFactory()
        other_question = QuestionFactory(product=other_product)

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        self.assertEqual(response.context["product"], product)

        # check we got our questions
        self.assertContains(response, question_1.question)
        self.assertContains(response, question_2.question)
        self.assertNotContains(response, other_question.question)

        # check ordering: Q1 comes after Q2
        q1_pos = response.text.index(question_1.question)
        q2_pos = response.text.index(question_2.question)
        self.assertGreater(q1_pos, q2_pos)

        # check if the menu item shows
        self.assertTrue(response.pyquery('.anchor-menu a[href="#faq"]'))
        # check if the menu link target
        self.assertTrue(response.pyquery("#faq"))


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestProductContent(WebTest):
    def test_button_is_rendered_inside_content_when_link_and_cta_exist(self):
        product = ProductFactory(
            content="Some content [CTABUTTON]", link="http://www.example.com"
        )

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        cta_button = response.pyquery(".grid__main")[0].find_class("cta-button")

        self.assertTrue(cta_button)
        self.assertIn(product.link, cta_button[0].values())

    def test_button_is_rendered_inside_content_when_form_and_cta_exist(self):
        product = ProductFactory(content="Some content [CTABUTTON]", form="demo")

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        cta_button = response.pyquery(".grid__main")[0].find_class("cta-button")

        self.assertTrue(cta_button)
        self.assertIn(product.form_link, cta_button[0].values())

    def test_button_is_rendered_inside_content_when_form_and_link_and_cta_exist(self):
        product = ProductFactory(
            content="Some content [CTABUTTON]",
            link="http://www.example.com",
            form="demo",
        )

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        cta_button = response.pyquery(".grid__main")[0].find_class("cta-button")

        self.assertTrue(cta_button)
        self.assertIn(product.link, cta_button[0].values())

    def test_button_is_not_rendered_inside_content_when_no_cta(self):
        product = ProductFactory(content="Some content", link="http://www.example.com")

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        cta_button = response.pyquery(".grid__main")[0].find_class("cta-button")

        self.assertFalse(cta_button)

    def test_button_is_not_rendered_inside_content_when_no_form_or_link(self):
        product = ProductFactory(content="Some content [CTABUTTON]")

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        cta_button = response.pyquery(".grid__main")[0].find_class("cta-button")

        self.assertFalse(cta_button)

    def test_button_text_change(self):
        """
        Assert that button text can be modified + aria-labels are changed accordingly
        """
        product = ProductFactory(
            content="Some content [CTABUTTON]",
            link="http://www.example.com",
            button_text="click me!",
        )

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )

        cta_button = response.pyquery(".grid__main")[0].find_class("cta-button")[0]
        cta_button_span = cta_button.getchildren()[0]

        self.assertEqual(cta_button.tag, "a")
        self.assertEqual(cta_button.attrib["title"], "click me!")
        self.assertEqual(cta_button.attrib["aria-label"], "click me!")
        self.assertEqual(cta_button_span.attrib["aria-label"], "click me!")

    def test_sidemenu_button_is_not_rendered_when_cta_inside_product_content(self):
        product = ProductFactory(
            content="Some content \[CTABUTTON\]", link="http://www.example.com"
        )

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        sidemenu_cta_button = response.pyquery(
            '.anchor-menu__list-item a[href="http://www.example.com"]'
        )

        self.assertFalse(sidemenu_cta_button)

    def test_sidemenu_button_is_rendered_when_no_cta_inside_product_content(self):
        product = ProductFactory(content="Some content", link="http://www.example.com")

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        sidemenu_cta_button = response.pyquery(
            '.anchor-menu__list-item a[href="http://www.example.com"]'
        )

        self.assertTrue(sidemenu_cta_button)
        self.assertIn(product.link, sidemenu_cta_button[0].values())

    def test_content_html_escape(self):
        product = ProductFactory()

        product.content = "hello \\<b>world\\</b> **test**"
        product.save()

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )

        self.assertNotContains(response, "hello world")
        self.assertNotContains(response, escape("<b>world"))
        self.assertContains(response, "hello <b>world</b>")
        self.assertContains(response, "<strong>test</strong>")


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestProductVideo(WebTest):
    def test_product_video_is_rendered(self):
        video = VideoFactory()
        product = ProductFactory(
            content="Some content",
            link="http://www.example.com",
            video=video,
        )
        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )
        video_frames = response.pyquery(".video iframe")
        self.assertEqual(len(video_frames), 1)
        iframe = video_frames[0]
        self.assertEqual(iframe.attrib["src"], video.player_url)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestProductDetailView(WebTest):
    def test_subheadings_in_sidebar(self):
        product = ProductFactory(
            content="##First subheading\rlorem ipsum...\r##Second subheading",
            link="http://www.example.com",
        )

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )

        links = response.pyquery(".anchor-menu__list .link")

        # 2 x 2 links (mobile + desktop)
        self.assertEqual(len(links), 4)

        self.assertEqual(links[0].text, "First subheading")
        self.assertEqual(links[0].attrib["href"], "#subheading-first-subheading")

        self.assertEqual(links[1].text, "Second subheading")
        self.assertEqual(links[1].attrib["href"], "#subheading-second-subheading")

        self.assertEqual(links[2].text, "First subheading")
        self.assertEqual(links[2].attrib["href"], "#subheading-first-subheading")

        self.assertEqual(links[3].text, "Second subheading")
        self.assertEqual(links[3].attrib["href"], "#subheading-second-subheading")


@tag("e2e")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@patch("open_inwoner.configurations.models.SiteConfiguration.get_solo")
class ProductPagePlaywrightTests(ClearCachesMixin, PlaywrightSyncLiveServerTestCase):
    def test_click_cta_button(self, mock_solo):
        mock_solo.return_value.cookiebanner_enabled = False

        product = ProductFactory(
            content="Some content [CTABUTTON]", link="http://www.example.com"
        )

        context = self.browser.new_context()
        page = context.new_page()

        page.goto(
            self.live_reverse("products:product_detail", kwargs={"slug": product.slug})
        )

        cta_button = page.locator(".grid__main .cta-button")

        expect(cta_button).to_be_visible()

        cta_button.click()
        new_page = context.wait_for_event("page")

        self.assertEqual(new_page.url, "http://www.example.com/")
