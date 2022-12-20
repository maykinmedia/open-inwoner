from django.template.exceptions import TemplateSyntaxError
from django.test import TestCase
from django.utils.translation import gettext as _

from open_inwoner.components.utils import RenderableTag


class RenderableTagTests(TestCase):
    maxDiff = None

    def test_non_existing_tag_raises_syntax_error(self):
        tag = RenderableTag("testing_tags", "non_existing_tag")

        with self.assertRaises(TemplateSyntaxError):
            tag.render()

    def test_simple_test_tag(self):
        tag = RenderableTag("testing_tags", "simple_test_tag")
        actual = tag.render()
        # django auto-escape still works
        expected = "I&#x27;m a simple tag!"
        self.assertEqual(actual, expected)

    def test_inclusion_test_tag(self):
        tag = RenderableTag("testing_tags", "inclusion_test_tag")
        actual = tag.render({"content": "Hello world!"})
        expected = f"""
        <div>
            <p>{_('Yes')}</p>
            <p>Hello world!</p>
        </div>
        """
        self.assertHTMLEqual(actual, expected)

    def test_inclusion_test_tag_without_kwargs_raises_syntax_error_on_extra_args(self):
        tag = RenderableTag("testing_tags", "inclusion_test_tag")
        with self.assertRaises(TemplateSyntaxError):
            tag.render({"content": "Hello world!", "extra_unused_arg": "foo"})

    def test_nested_tag(self):
        tag = RenderableTag("testing_tags", "nested_test_tag")
        actual = tag.render({"title": "Welcome", "content": "Hello world!"})
        expected = f"""
        <div>
            <h1>Welcome</h1>
            <p>I&#x27;m a simple tag!</p>
            <div>
                <p>{_('Yes')}</p>
                <p>Hello world!</p>
            </div>
        </div>
        """
        self.assertHTMLEqual(actual, expected)

    def test_nested_tag_with_default(self):
        tag = RenderableTag("testing_tags", "nested_test_tag")
        actual = tag.render({"title": "Welcome"})
        expected = f"""
        <div>
            <h1>Welcome</h1>
            <p>I&#x27;m a simple tag!</p>
            <div>
                <p>{_('Yes')}</p>
                <p>default</p>
            </div>
        </div>
        """
        self.assertHTMLEqual(actual, expected)

    def test_nested_tag_with_kwargs_allows_extra_args(self):
        tag = RenderableTag("testing_tags", "nested_test_tag")
        actual = tag.render(
            {"title": "Welcome", "content": "Hello world!", "extra_unused_arg": "foo"}
        )
        expected = f"""
        <div>
            <h1>Welcome</h1>
            <p>I&#x27;m a simple tag!</p>
            <div>
                <p>{_('Yes')}</p>
                <p>Hello world!</p>
            </div>
        </div>
        """
        self.assertHTMLEqual(actual, expected)
