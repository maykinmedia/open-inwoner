from django import template
from django.utils.html import format_html

import markdown
from bs4 import BeautifulSoup

register = template.Library()


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)
