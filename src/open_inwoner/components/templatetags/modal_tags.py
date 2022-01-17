from django import template

register = template.Library()


@register.inclusion_tag("components/Modal/Modal.html")
def show_help(current_path, help, **kwargs):
    """
    Shows the appropriate help message depending on the current page.

    Usage:
        {% show_help current_path=current_path help=help %}

    Variables:
        + current_path: str | the current path.
        + help: obj | the object containing the different types of help texts.
    """

    def get_help_type():
        if current_path == "/":
            return "home_help"
        if "/themas/" in current_path:
            return "theme_help"
        if "/products/" in current_path:
            return "product_help"
        if "/search/" in current_path:
            return "search_help"
        if "/accounts/" in current_path:
            return "account_help"

    kwargs["help_type"] = get_help_type()

    return {**kwargs, "current_path": current_path, "help": help}
