from typing import Optional

from django import template
from django.template import Context, Template
from django.template.library import InclusionNode, parse_bits
from django.template.loader import render_to_string


class ContentsNode(template.Node):
    def __init__(self, nodelist, template_name, context_func=None, **kwargs):
        self.nodelist = nodelist
        self.template_name = template_name
        self.context_func = context_func
        self.kwargs = kwargs

    def render(self, context):
        corrected_kwargs = {
            key: safe_resolve(kwarg, context) for key, kwarg in self.kwargs.items()
        }
        if self.context_func:
            context_kwargs = self.context_func(context=context, **corrected_kwargs)
        else:
            context_kwargs = corrected_kwargs
        output = self.nodelist.render(context)
        render_context = {
            "contents": output,
            **context_kwargs,
        }
        rendered = render_to_string(self.template_name, render_context)
        return rendered


def parse_component_with_args(parser, bits, tag_name):
    tag_args, tag_kwargs = parse_bits(
        parser=parser,
        bits=bits,
        params=["tag_name"],
        takes_context=False,
        name=tag_name,
        varargs=True,
        varkw=[],
        defaults=None,
        kwonly=[],
        kwonly_defaults=None,
    )
    return tag_kwargs


def safe_resolve(context_item, context):
    """Resolve FilterExpressions and Variables in context if possible.  Return other items unchanged."""

    return (
        context_item.resolve(context)
        if hasattr(context_item, "resolve")
        else context_item
    )


class ComponentNode:
    """
    A component node that either renders an InclusionNode or a ContentsNode.

    Usage:
        @register.tag()
        def new_tag(parser, token):
            def context_func(context, variable1, **kwargs):
                _context = context.flatten()
                kwargs.update(variable1=variable1)
                return {**_context, **kwargs}

            node = ComponentNode(
                "tag_name",
                "template/location.html",
                parser,
                token,
                context_func,
            )
            return node.render()

    Hopefully this can be improved in the future. But it is a good start.
    """

    def __init__(self, tag_name, template_name, parser, token, context_func):
        self.tag_name = tag_name
        self.template_name = template_name
        self.parser = parser
        self.token = token
        self.context_func = context_func

    def render(self):
        endtag_name = f"end{self.tag_name}"
        has_ending = False
        for t in self.parser.tokens:
            if endtag_name in t.contents:
                has_ending = True
        function_name = self.tag_name

        if has_ending:
            nodelist = self.parser.parse((endtag_name,))
            bits = self.token.split_contents()
            args, kwargs = parse_bits(
                self.parser,
                bits,
                ["context"],
                True,
                [],
                None,
                [],
                None,
                True,
                function_name,
            )
            self.parser.delete_first_token()
            return ContentsNode(
                nodelist, self.template_name, self.context_func, **kwargs
            )
        else:
            bits = self.token.split_contents()[1:]
            args, kwargs = parse_bits(
                self.parser,
                bits,
                ["context"],
                True,
                [],
                None,
                [],
                None,
                True,
                function_name,
            )
            return InclusionNode(
                self.context_func,
                True,
                args,
                kwargs,
                self.template_name,
            )


class RenderableTag:
    """
    Render a template tag to string

    based on InclusionTagWebTest

        Usage:
            tag = RenderableTag("my_custom_tags", "my_tag")
            html = tag.render({"some_argument": "value", "request": request})
    """

    def __init__(self, library_name: str, tag_name: str):
        self.library = library_name
        self.tag = tag_name

    def __call__(self, **kwargs) -> str:
        """
        Renders the template tag with given keyword arguments.

        Args:
            **kwargs: Every argument that should be passed to the tag.

        Returns: The str rendered by the tag.
        """
        return self.render(kwargs)

    def render(self, tag_args: Optional[dict] = None) -> str:
        """
        Renders the template tag with arguments.

        Args:
            tag_args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: The str rendered by the tag.
        """
        tag_args = tag_args or {}
        template_context = self.get_template_context(tag_args)
        context = Context(template_context)
        template = self.get_template(tag_args)
        return template.render(context)

    def get_template(self, tag_args: Optional[dict] = None):
        """
        Returns the (Django) Template instance (in order to render the tag).
        A templates str is constructed and then passed to a django.template.Template, the resulting instance is
        returned.

        Args:
            tag_args: Optional, a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: django.template.Template
        """
        tag_args = self.get_args(tag_args or {})
        template = (
            "{% load "
            + self.library
            + " %}{% "
            + self.tag
            + " "
            + tag_args
            + " "
            + " %}"
        )
        return Template(template)

    def get_args(self, tag_args: dict) -> str:
        """
        Returns a str with variable assignments in a format suitable for template rendering.
        Values in args may not be directly passed but might also refer to template_context_<key>. The variable may then
        be provided by `get_template_context()` and passed to the Template (provided by `get_template`) by `render()`.

        Args:
            tag_args: a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: A str with variable assignments in a format suitable for template rendering
        """
        args_list = []

        for k, v in tag_args.items():
            if isinstance(v, (int, float)):
                args_list.append(f"{k}={v}")
                continue
            elif isinstance(v, (str,)):
                args_list.append(f'{k}="{v}"')
                continue
            args_list.append(f"{k}=template_context_{k}")

        return " ".join(args_list)

    def get_template_context(self, tag_args: dict) -> dict:
        """
        Returns the context required to render the template.
        Args:
            tag_args: a dict containing a key+value mapping of every argument that should be passed to the tag.

        Returns: A dict representing the template context.

        """
        template_context = {}

        for k, v in tag_args.items():
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
