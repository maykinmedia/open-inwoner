from django.utils.encoding import force_str
from django.utils.html import conditional_escape, format_html


def middle_truncate(value: str, length: int, dots="...") -> str:
    if len(value) <= length:
        return value
    half = int(length / 2)
    return f"{value[: half - len(dots)]}{dots}{value[-half:]}"


def html_tag_wrap_format(format_str: str, tag: str, **kwargs) -> str:
    assert kwargs, "expected replacment kwargs"
    html_tag = "<{}>{{}}</{}>".format(tag, tag)
    replace = {
        name: format_html(html_tag, force_str(value)) for name, value in kwargs.items()
    }
    text = conditional_escape(format_str)
    return format_html(text, **replace)
