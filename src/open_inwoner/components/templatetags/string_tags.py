from django import template
from django.utils.html import format_html
from bs4 import BeautifulSoup
import markdown

register = template.Library()


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter()
def markdown2html(value):
    md = markdown.Markdown(extensions=["tables"])
    html = md.convert(value)
    soup = BeautifulSoup(html, "html.parser")
    class_adders = [
        ("h1", "h1"),
        ("h2", "h2"),
        ("h3", "h3"),
        ("h4", "h4"),
        ("h5", "h5"),
        ("h6", "h6"),
        ("img", "image"),
        ("li", "li"),
        ("p", "p"),
        ("a", "link link--secondary"),
        ("table", "table table--content"),
        ("th", "table__header"),
        ("td", "table__item"),
    ]
    for tag, class_name in class_adders:
        for element in soup.find_all(tag):
            element.attrs["class"] = class_name

    return str(soup)
