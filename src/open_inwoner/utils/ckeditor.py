import markdown
from bs4 import BeautifulSoup

from open_inwoner.pdc.models.product import Product


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
            if element.text.startswith("[CTA/"):
                product_slug = element.text.split("/")[1][:-1]
                try:
                    product = Product.objects.get(slug=product_slug)
                except Product.DoesNotExist:
                    element.decompose()
                    continue

                icon = soup.new_tag("span")
                icon.attrs.update(
                    {"aria-label": "Aanvraag starten", "class": "material-icons"}
                )
                icon.append("arrow_forward")
                element.string.replace_with("Aanvraag starten")
                element.attrs.update(
                    {
                        "class": "button button--textless button--icon button--icon-before button--primary",
                        "href": f"{product.get_absolute_url()}/formulier",
                    }
                )
                element.attrs["title"] = "Aanvraag starten"
                element.append(icon)

    return soup
