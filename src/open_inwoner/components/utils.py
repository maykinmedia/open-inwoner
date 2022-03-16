from django import template
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
