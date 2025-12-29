from django.utils.text import slugify

import markdown
from bs4 import BeautifulSoup

PRODUCT_PATH_NAME = "products"


def extract_subheadings(content, tag: str) -> list[tuple[str, str]]:
    """
    Returns a list of tuples containing a subheading (the text of the `tag` element)
    and a slug for the corresponding HTML anchor.

    Supports both legacy string content (TextField) and ProsemirrorModelField.
    """
    # Check if content is a string
    if isinstance(content, str):
        # Legacy markdown conversion for old TextField content
        md = markdown.Markdown()
        html_string = md.convert(content)
    else:
        # ProsemirrorModelField - use .html property
        html_string = content.html

    soup = BeautifulSoup(html_string, "html.parser")

    subs = []
    for element in soup.find_all("h2"):
        subheading = element.text
        slug = f"#subheading-{slugify(subheading)}"
        subs.append((slug, subheading))

    return subs
