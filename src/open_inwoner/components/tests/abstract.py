from django.template import Context, Template
from django.test import RequestFactory

from bs4 import BeautifulSoup
from django_webtest import WebTest


class InclusionTagWebTest(WebTest):
    library = ""  # {% load my_library %}
    tag = ""  # {% my_tag %}

    def assertContext(self, config={}):
        context = self.call_function()
        self.assertTrue(context)

    def assertRender(self, config={}, data={}):
        html = self.render(config, data)
        self.assertTrue(html)

    def assertSelector(self, selector, config={}, data={}):
        node = self.select(selector, config, data)
        self.assertTrue(node)
        return node

    def assertNotSelector(self, selector, config={}, data={}):
        node = self.select(selector, config, data)
        self.assertFalse(node)
        return node

    def assertTextContent(self, selector, text, config={}, data={}):
        node = self.select_one(selector, config, data)
        self.assertEqual(str(text).strip(), node.text.strip())

    def render(self, config={}, data={}):
        config = config or {}
        context = Context(
            {**config, "request": RequestFactory().get("/foo", data)}
        )
        template = self.get_template(config)
        return template.render(context)

    def select_one(self, selector, config={}, data={}):
        html = self.render(config, data)
        soup = BeautifulSoup(html, features="lxml")
        return soup.select_one(selector)

    def select(self, selector, config={}, data={}):
        html = self.render(config, data)
        soup = BeautifulSoup(html, features="lxml")
        return soup.select(selector)

    def call_function(self, config={}):
        template = self.get_template(config)
        nodelist = template.compile_nodelist()
        inclusion_node = nodelist[1]
        function = inclusion_node.func
        return function(**config)

    def get_template(self, config={}):
        args = self.get_args(config)
        template = "{% load " + self.library + " %}{% " + self.tag + " " + args + " " + "config=config %}"
        return Template(template)

    def get_args(self, config):
        args = []

        for k, v in config.items():
            if v.isnumeric():
                args.append(f"{k}={v}")
                continue
            args.append(f'{k}="{v}"')

        return " ".join(args)


class ContentsTagWebTest(InclusionTagWebTest):
    contents = ""  # {% my_tag %}{{ my contents }}{% endmytag %}

    def assertContents(self, config={}, data={}, contents_context={}):
        html = self.render(config, data)
        context = Context(contents_context)
        self.assertIn(self.get_contents(context), html)

    def get_contents(self, context={}):
        return Template("{% load " + self.library + " %}" + self.contents).render(context)

    def get_template(self, config={}):
        args = self.get_args(config)
        template = "{% load " + self.library + " %}{% " + self.tag + " " + args + " " + "config=config %}" + self.contents + "{% end" + self.tag + " %}"
        return Template(template)
