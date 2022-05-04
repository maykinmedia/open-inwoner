import markdown
from bs4 import BeautifulSoup


def get_rendered_content(content):
    """
    Takes object's content as an input and returns the rendered one.
    """
    md = markdown.Markdown(extensions=["tables"])
    html = md.convert(content)
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

    return soup
