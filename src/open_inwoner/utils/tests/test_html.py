from django.test import SimpleTestCase, TestCase, override_settings

from open_inwoner.pdc.tests.factories import QuestionFactory
from open_inwoner.utils.html import get_rendered_content, is_safe_url, sanitize_html


class IsSafeUrlTest(SimpleTestCase):
    def test_allows_http_and_https(self):
        self.assertTrue(is_safe_url("http://example.com"))
        self.assertTrue(is_safe_url("https://example.com"))

    def test_allows_mailto_and_tel(self):
        self.assertTrue(is_safe_url("mailto:info@example.com"))
        self.assertTrue(is_safe_url("tel:+31612345678"))

    def test_allows_relative_and_fragment_links(self):
        self.assertTrue(is_safe_url("/some/path"))
        self.assertTrue(is_safe_url("#anchor"))
        self.assertTrue(is_safe_url("?query=1"))

    def test_blocks_javascript_scheme(self):
        self.assertFalse(is_safe_url("javascript:alert(document.cookie)"))
        self.assertFalse(is_safe_url("JaVaScRiPt:alert(1)"))

    def test_blocks_data_and_vbscript_schemes(self):
        self.assertFalse(is_safe_url("data:text/html;base64,PHNjcmlwdD4="))
        self.assertFalse(is_safe_url("vbscript:msgbox(1)"))

    def test_blocks_empty_url(self):
        self.assertFalse(is_safe_url(""))


class SanitizeHtmlTest(SimpleTestCase):
    def test_strips_javascript_href(self):
        html = '<p><a href="javascript:alert(1)">click</a></p>'

        result = sanitize_html(html)

        self.assertNotIn("javascript:", result)
        self.assertIn("click", result)

    def test_keeps_safe_href(self):
        html = '<p><a href="https://example.com">click</a></p>'

        result = sanitize_html(html)

        self.assertIn('href="https://example.com"', result)

    def test_handles_empty_input(self):
        self.assertEqual(sanitize_html(""), "")
        self.assertEqual(sanitize_html(None), None)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class GetRenderedContentLinkSanitizationTest(TestCase):
    def test_faq_answer_with_javascript_link_is_sanitized(self):
        question = QuestionFactory.create()
        question.answer.html = (
            '<p><a href="javascript:alert(document.cookie)">click me</a></p>'
        )
        question.save()

        rendered = get_rendered_content(question.answer)

        self.assertNotIn("javascript:", rendered)
        self.assertIn("click me", rendered)

    def test_faq_answer_with_safe_link_is_preserved(self):
        question = QuestionFactory.create()
        question.answer.html = '<p><a href="https://example.com">click me</a></p>'
        question.save()

        rendered = get_rendered_content(question.answer)

        self.assertIn('href="https://example.com"', rendered)
        self.assertIn("click me", rendered)
