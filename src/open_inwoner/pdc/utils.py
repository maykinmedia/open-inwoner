from django.utils.text import slugify

import markdown
from bs4 import BeautifulSoup

PRODUCT_PATH_NAME = "products"


def extract_subheadings(content: str, tag: str) -> list[tuple[str, str]]:
    """
    :returns: a list of tuples containing a subheading (the text of the `tag` element)
    and a slug for the corresponding HTML anchor
    """
    md = markdown.Markdown()
    html_string = md.convert(content)

    soup = BeautifulSoup(html_string, "html.parser")

    subs = []
    for tag in soup.find_all("h2"):
        subheading = tag.text
        slug = slugify(subheading)
        subs.append((subheading, slug))

    return subs
