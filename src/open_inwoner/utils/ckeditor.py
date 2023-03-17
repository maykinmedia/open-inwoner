import markdown
from bs4 import BeautifulSoup

CLASS_ADDERS = [
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


def get_rendered_content(content):
    """
    Takes object's content as an input and returns the rendered one.
    """
    md = markdown.Markdown(extensions=["tables"])
    html = md.convert(content)
    soup = BeautifulSoup(html, "html.parser")

    for tag, class_name in CLASS_ADDERS:
        for element in soup.find_all(tag):
            element.attrs["class"] = class_name
            if element.name == "a" and element.attrs.get("href", "").startswith("http"):
                element.attrs["target"] = "_blank"

    return soup


def get_product_rendered_content(product):
    """
    Takes product's content as an input and returns the rendered one.
    """
    md = markdown.Markdown(extensions=["tables"])
    html = md.convert(product.content)
    soup = BeautifulSoup(html, "html.parser")

    for tag, class_name in CLASS_ADDERS:
        for element in soup.find_all(tag):
            if element.attrs.get("class") and "cta-button" in element.attrs["class"]:
                continue

            element.attrs["class"] = class_name

            if "[CTABUTTON]" in element.text:
                # decompose the element when product doesn't have either a link or a form
                if not (product.link or product.form):
                    element.decompose()
                    continue

                # icon
                icon = soup.new_tag("span")
                icon.attrs.update(
                    {"aria-label": "Aanvraag starten", "class": "material-icons"}
                )
                icon.append("arrow_forward")

                # button
                element.name = "a"

                element.string.replace_with("Aanvraag starten")
                element.attrs.update(
                    {
                        "class": "button button--textless button--icon button--icon-before button--primary cta-button",
                        "href": (
                            product.link
                            if product.link
                            else f"{product.get_absolute_url()}formulier"
                        ),
                        "title": "Aanvraag starten",
                    }
                )
                element.append(icon)

                if product.link:
                    element.attrs.update({"target": "_blank"})

            if element.name == "a" and element.attrs.get("href", "").startswith("http"):
                icon = soup.new_tag("span")
                icon.attrs.update(
                    {
                        "aria-hidden": "true",
                        "aria-label": "Opens in new window",
                        "class": "material-icons",
                    }
                )
                icon.append("open_in_new")
                element.append(icon)

    return soup
