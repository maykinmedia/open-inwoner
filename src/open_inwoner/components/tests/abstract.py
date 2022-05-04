from typing import Union

from django.template import Context, Template
from django.test import RequestFactory

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from django_webtest import WebTest


class InclusionTagWebTest(WebTest):
    """
    Tests class for inclusion tags.

    This class contains methods to test inclusion tags, for tags that use ContentsNode to render contents (children) use
    ContentsTagWebTest.

    In order to test a tag, extend this class and set `library` and `tag` to their correct values. Then use any of the
    assertion methods to test the tag.

    A special variable "args" (dict) is available for most/all methods and should contain a key+value mapping of every
    argument passed to the tag.

    Example:

        class TestListItem(InclusionTagWebTest):
            library = "list_tags"
            tag = "list_item"

            def test_render(self):
                self.assertRender({"text": "Lorem ipsum"})

            def test_text(self):
                self.assertTextContent("h4", "Lorem ipsum", {"text": "Lorem ipsum"})

            def test_description(self):
                self.assertTextContent(
                    "p", "Dolor sit", {"text": "Lorem ipsum", "description": "Dolor sit"}
                )

            def test_href(self):
                self.assertNotSelector("a", {"text": "Lorem ipsum", "description": "Dolor sit"})
                a = self.assertSelector(
                    "h4 a",
                    {
                        "text": "Lorem ipsum",
                        "description": "Dolor sit",
                        "href": "https://www.example.com",
                    },
                )
                self.assertEqual(a[0]["href"], "https://www.example.com")
    """

    # The library name, a value of "list_tags" would be the equivalent of "{% load list_tags %}".
    library = ""

    # The tag name, a value of "list_item" would be the equivalent of "{% list_item %}".
    tag = ""

    def assertContext(self, args: dict = {}) -> any:
        """
        Asserts that a context is returned by the inclusion tag.

        Args:
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: The return value of the tag's function.
        """
        context = self.call_function(args)
        self.assertTrue(context)
        return context

    def assertRender(self, args: dict = {}, data={}) -> str:
        """
        Asserts that something is rendered by the tag.

        Args:
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: A dict containing a key+value mapping of every item that should be passed to the RequestFactory's
                  query string.

        Returns: The str rendered by the tag.
        """
        html = self.render(args, data)
        self.assertTrue(html)
        return html

    def assertSelector(
        self, selector: str, args: dict = {}, data: dict = {}
    ) -> ResultSet:
        """
        Asserts that an HTML tag matching `selector` is present in the tag's rendered output.

        Args:
            selector: A str, the (CSS style) selector.
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: Optional, a dict containing a key+value mapping of every item that should be passed to the
                  RequestFactory's query string.

        Returns: bs4.element.ResultSet
        """
        nodes = self.select(selector, args, data)
        self.assertTrue(nodes, msg=f"Did not find selector {selector}")
        return nodes

    def assertNotSelector(
        self, selector: str, args: dict = {}, data: dict = {}
    ) -> ResultSet:
        """
        Asserts that an HTML tag matching `selector` is not present in the tag's rendered output.

        Args:
            selector: A str, the (CSS style) selector.
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: Optional, a dict containing a key+value mapping of every item that should be passed to the
                  RequestFactory's query string.

        Returns: bs4.element.ResultSet
        """
        nodes = self.select(selector, args, data)
        self.assertFalse(nodes)
        return nodes

    def assertTextContent(
        self, selector: str, text: str, args: dict = {}, data: dict = {}
    ) -> str:
        """
        Asserts that an HTML tag matching `selector` has textual content matching `text`.

        Args:
            selector: A str, the (CSS style) selector.
            text: A str, the expected textual content of the HTML tag matching `selector`.
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: Optional, a dict containing a key+value mapping of every item that should be passed to the
                  RequestFactory's query string.

        Returns: bs4.element.ResultSet
        """
        node = self.select_one(selector, args, data)
        self.assertEqual(str(text).strip(), node.text.strip())
        return node.text

    def render(self, args={}, data={}):
        """
        Renders the template tag with arguments (and optionally passing `data` to RequestFactory's query string).

        Args:
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: Optional, a dict containing a key+value mapping of every item that should be passed to the
                  RequestFactory's query string.

        Returns: The str rendered by the tag.
        """
        args = args or {}
        template_context = self.get_template_context(args)
        context = Context(
            {**template_context, "request": RequestFactory().get("/foo", data)}
        )
        template = self.get_template(args)
        return template.render(context)

    def select_one(self, selector: str, args: dict = {}, data: dict = {}) -> Tag:
        """
        Returns a bs4.element.Tag for HTML tag matching `selector` within the str rendered by the tag.

        Args:
            selector: A str, the (CSS style) selector.
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: Optional, a dict containing a key+value mapping of every item that should be passed to the
                  RequestFactory's query string.

        Returns: bs4.element.Tag
        """
        html = self.render(args, data)
        soup = BeautifulSoup(html, features="lxml")
        return soup.select_one(selector)

    def select(self, selector: str, args: dict = {}, data: dict = {}) -> ResultSet:
        """
        Returns a bs4.element.ResultSet for HTML tags matching `selector` within the str rendered by the tag.

        Args:
            selector: A str, the (CSS style) selector.
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: Optional, a dict containing a key+value mapping of every item that should be passed to the
                  RequestFactory's query string.

        Returns: bs4.element.ResultSet
        """
        html = self.render(args, data)
        soup = BeautifulSoup(html, features="lxml")
        return soup.select(selector)

    def call_function(self, args: dict = {}) -> any:
        """
        Calls the tag's function directly.

        Args:
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: The return value of the tag's function.
        """
        template = self.get_template(args)
        nodelist = template.compile_nodelist()
        inclusion_node = nodelist[1]
        function = inclusion_node.func
        return function(**args)

    def get_template(self, args={}):
        """
        Returns the (Django) Template instance (in order to render the tag).
        A templates str is constructed and then passed to a django.template.Template, the resulting instance is
        returned.

        Args:
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: django.template.Template
        """
        args = self.get_args(args)
        template = (
            "{% load " + self.library + " %}{% " + self.tag + " " + args + " " + " %}"
        )
        return Template(template)

    def get_args(self, args: dict) -> str:
        """
        Returns a str with variable assignments in a format suitable for template rendering.
        Values in args may not be directly passed but might also refer to template_context_<key>. The variable may then
        be provided by `get_template_context()` and passed to the Template (provided by `get_template`) by `render()`.

        Args:
            args: a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: A str with variable assignments in a format suitable for template rendering
        """
        args_list = []

        for k, v in args.items():
            if isinstance(
                v,
                (
                    int,
                    float,
                ),
            ):
                args_list.append(f"{k}={v}")
                continue
            elif isinstance(v, (str,)):
                args_list.append(f'{k}="{v}"')
                continue
            args_list.append(f"{k}=template_context_{k}")

        return " ".join(args_list)

    def get_template_context(self, args: dict) -> dict:
        """
        Returns the context required to render the template.
        Args:
            args: a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: A dict representing the template context.

        """
        template_context = {}

        for k, v in args.items():
            if isinstance(
                v,
                (
                    str,
                    int,
                    float,
                ),
            ):
                continue
            template_context[f"template_context_{k}"] = v

        return template_context


class ContentsTagWebTest(InclusionTagWebTest):
    """
    Tests class for contents tags.

    This class contains methods to test content tags, for tags that don't use ContentsNode to render contents (children)
    use InclusionTagWebTest.

    In order to test a tag, extend this class and set `library` and `tag` and optionally `contents` to their correct
    values. Then use any of the
    assertion methods to test the tag.

    A special variable "args" (dict) is available for most/all methods and should contain a key+value mapping of every
    argument passed to the tag.

    Example:

        class TestList(ContentsTagWebTest):
            library = "list_tags"
            tag = "render_list"
            contents = '{% list_item text="Lorem ipsum" %}'

            def test_render(self):
                self.assertRender()

            def test_contents(self):
                self.assertContents()
    """

    # The library name, a value of "list_tags" would be the equivalent of "{% load list_tags %}".
    library = ""

    # The tag name, a value of "render_list" would be the equivalent of "{% render_list %}{% endrender_list %}".
    tag = ""

    # The tag contents, if another tag template (str) is passed, it must be from the sames library as tag.
    # A value of "{% list_item %}" would be the equivalent of "{% render_list %}{% list_item %}{% endrender_list %}".
    contents = ""

    def assertContents(self, args={}, data={}, contents_context={}) -> str:
        """
        Asserts that rendered HTML of contents is present in the tag's rendered output.

        Args:
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.
            data: Optional, a dict containing a key+value mapping of every item that should be passed to the
                  RequestFactory's query string.
            contents_context: Optional, a dict for the context passed while rendering the contents.

        Returns: The contents html.
        """
        html = self.render(args, data)
        context = Context(contents_context)
        contents_html = self.get_contents(context)
        self.assertIn(contents_html, html)
        return contents_html

    def get_contents(self, context: Union[Context, dict] = {}) -> str:
        """
        Renders contents HTML.

        Args:
            context: Optional, a Context or dict for the context passed while rendering the contents.

        Returns: The contents html.
        """
        return Template("{% load " + self.library + " %}" + self.contents).render(
            context
        )

    def get_template(self, args={}):
        """
        Returns the (Django) Template instance (in order to render the tag).
        A templates str is constructed and then passed to a django.template.Template, the resulting instance is
        returned.

        Args:
            args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: django.template.Template
        """
        args = self.get_args(args)
        template = (
            "{% load "
            + self.library
            + " %}{% "
            + self.tag
            + " "
            + args
            + " "
            + " %}"
            + self.contents
            + "{% end"
            + self.tag
            + " %}"
        )
        return Template(template)
