# Components
This app contains the UI elements of the project implemented as inclusion tags.

> Components are the reusable building blocks of our design system. Each component meets a specific interaction or UI
> need, and has been specifically created to work together to create patterns and intuitive user experiences. - [Atlassian Design System](https://atlassian.design/components/)

## Contents

- [What are inclusion tags](#what-are-inclusion-tags)
- [Why do we use inclusion tags](#why-do-we-use-inclusion-tags)
- [When writing inclusion tags](#when-writing-inclusion-tags)
- [Nesting tags](#nesting-tags)
- [Writing tests](#writing-tests)
- [Known issues](#known-issues)
- [Further reading](#further-reading)

<a id="what-are-inclusion-tags"/></a>
## What are inclusion tags?
Inclusion tags are a mechanism in Django te render a (small) template based on (optionally) a set of arguments. We use
these tags te create the individual building blocks of our interface, abstracting away the implementation
(HTMl/CSS/JavaScript) from their (programming) interface.

*Note: inclusion_tags are often referered to as "components". Components typically make up an inclusion tag, a template,
a Sass (`.scss`) and sometimes a JavaScript file.*

 > Another common type of template tag is the type that displays some data by rendering another template. For example,
 > Django’s admin interface uses custom template tags to display the buttons along the bottom of the “add/change” form pages. Those buttons always look the same, but the link targets change depending on the object being edited – so they’re a perfect case for using a small template that is filled with details from the current object. (In the admin’s case, this is the submit_row tag.) - [Django documentation](https://docs.djangoproject.com/en/4.0/howto/custom-template-tags/#howto-custom-template-tags-inclusion-tags)

Inclusion tags in Django are provided in "libraries" that can be registered in apps. Libraries are Python files that
register various template tags (like inclusion tags).

Django will automatically discover any librar(y/ies) in any app within their `templatetags` package. The libraries
provided by the `components` app can be found in `components/template_tags/`.

A library should instantiate a `Library` class and then register a function to it:

```python
# my_first_tags.py
from django import template

register = template.Library()


@register.inclusion_tag("components/MyFirstInclusionTag/MyFirstInclusionTag.html")
def my_first_inclusion_tag(foo, bar):
    """
    An example of an inclusion tag.

    Usage:
        {% my_first_inclusion_tag 'value_for_foo' 1 %}

    Variables:
        + foo: string | a `str` example argument 1.
        - bar: int | an `int` example argument 1.
    """
    return {"foo": foo, "bar": bar}
```

```html
<!-- components/MyFirstInclusionTag/MyFirstInclusionTag.html -->
<div class="my-first-inclusion-tag">
    <strong>foo:</strong>&nbsp;{{ foo }}
    <strong>bar:</strong>&nbsp;{{ bar }}
</div>
```

*(Creating a library might require a server restart.*

The library above exposes an inclusion tag `my_first_inclusion_tag` which would render
`components/MyFirstInclusionTag/MyFirstInclusionTag.html` with `{"foo": foo, "bar": bar}` as context.

The inclusion tag can be rendered anywhere using:

```django
{% load my_first_tags %}
{% my_first_inclusion_tag 'value_for_foo' 1 %}
```

<a id="why-do-we-use-inclusion-tags"/></a>
## Why do we use inclusion tags?
Inclusion tags have various benefits over traditional templates:

-  Inclusion tags are highly reusable.
-  Inclusion tags can ensure consistency of the UI by providing a single source of truth of the implementation.
-  Inclusion tags can do their own centralized context processing.
-  Inclusion tags can be tested with little dependencies.

Example:

Given an example of a hyperlink with an icon:

```html
{% load i18n %}
<a class="button button--primary" href="{% url 'accounts:inbox' %}">
    <span class="material-icon">arrow_forward</span>
    {% trans 'My messages' %}
</a>
```
This template may look simple at once, but contains various sources of logic that need to work together:

- Button styling.
- Icon styling.
- URL resolving.
- Translation.

Most of this logic can change anytime and such a change would require all usages to be updated. Such changes might be as
simple as a CSS file update that requires the HTML tree to be rendered differently (this invalidates all existing
implementations).

Replacing this link with a simple:

```django
{% load i18n %}
{% link href='accounts:inbox' text=_('My messages') button=True primary=True icon='arrow_forward' %}
```

Gives us the ability to alter (upgrade) the implementation anytime without worrying about the existing usages. As a
bonus: it allows us to do certain processing in the component (like url reversion) in the tag itself. Reducing workload
for the developer.

<a id="when-writing-inclusion-tags"/></a>
# When writing inclusion tags

Writing inclusion tags allows a developer to split a view into smaller pieces. Although this has various advantages,
please adhere to the following:

- Do maintain a stable (backwards compatible) signature for a template tag.
- Do: write docstrings for template tags explaining what they do and how they should be used.
- Do: write tests for your template tag (see: [writing tests](#writing-tests)).
- Do: "speak Django", use default object types (like QuerySet and Form) where possible and use names/structures similar
  to the world of Django (e.g. `object_list`, `page_obj` etc.).
- Do: be implementation agnostic: preferably, an inclusion tag should not depend on specific business logic/models.
- Don't: reinvent the wheel, handoff logic to Django builtin's (like paginaton) where possible.

<a id="nesting-tags"/></a>
# Nesting tags

### TODO: Nested tags might use refactoring/improvements.

Some tags (not inclusion tags) provide a way to nest other contents and tags as children. By convenstion, we prefix the
name of these tags with "render_"

> A nested component is a child of the parent component that contains it. The child component is positioned and rendered
> relative to that parent. The minimum size of a container component is determined by the size of its child components.- [Apple Developer Documentation](https://developer.apple.com/documentation/apple_news/apple_news_format/components/nesting_components_in_an_article)

Django, by default does not support a way of nesting inclusion tags. The components app provides a different way of
dealing with this using a `ContentsNode`. This will create a tag which accepts children between
`{% render_my_first_contents_node %}` and `{% endrender_my_first_contents_node %}`:

```python
@register.tag()
def render_my_first_contents_node(parser, token):  # Start tag
    """
    An example contents node.
    Nested content supported.

    Usage:
        {% render_my_first_contents_node %}
            Foo bar
        {% render_endmy_first_contents_node %}

    Extra context:
        - contents: string | The HTML content that is between the open and close tags,
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_list")
    nodelist = parser.parse(("endrender_my_first_contents_node",))  # End tag
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/MyFirstContentsNode/MyFirstContentsNode.html", **context_kwargs)  # Template
```

```html
<!-- components/MyFirstContentsNode/MyFirstContentsNode.html -->
<div class="my-first-contents-tag">
    {{ contents }}  <!-- Provided by ContentsNode, contains nested content (children). -->
</div>
```

<a id="writing-tests"/></a>
# Writing tests

Tests for components are located in the `tests` package of the components app (`components/tests/`). In this directory a
file called `abstract.py` can be found. This file contains utility classes that provide testing of tags:

- `InclusionTagWebTest` allows for testing inclusion tags.
- `ContentsTagWebTest` similar to  InclusionTagWebTest, but for content tags.

Please refer to the docstrings of their respective methods for usages.

### Examples:

These are some real world examples of testing inclusion tags:

Example 1 (`list_tags.render_list`):

```python
class TestList(ContentsTagWebTest):
    library = "list_tags"
    tag = "render_list"
    contents = '{% list_item text="Lorem ipsum" %}'

    def test_render(self):
        self.assertRender()

    def test_contents(self):
        self.assertContents()

```

Example 2 (`list_tags.list_item`):
```python
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
```

<a id="known-issues"></a>
# Known issues

### Inclusion tags don't get executed in all cases.
Some requests, for instance: POST requests, might not invoke template rendering and skip code in template tags. This
might complicate cases where processing of such requests is required.

A possible solution is to manually invoke template rendering from within the `post` method on the view, or to handle
this logic in a separate `url` and set that as the form's action.

<a id="further-reading"></a>
# Further reading

- https://docs.djangoproject.com/en/4.0/howto/custom-template-tags/
- https://docs.djangoproject.com/en/4.0/howto/custom-template-tags/#howto-custom-template-tags-inclusion-tags
- https://docs.djangoproject.com/en/4.0/ref/templates/builtins/
