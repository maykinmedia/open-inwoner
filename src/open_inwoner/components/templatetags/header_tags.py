from django import template

from open_inwoner.configurations.models import SiteConfiguration

register = template.Library()


@register.inclusion_tag("components/Header/AccessibilityHeader.html")
def accessibility_header(request, **kwargs):
    """
    This is used to display the accessibility header
    Usage:
        {% accessibility_header request=request%}
    Variables:
        + request: Request | The django request object.
    Extra context:
        - help_text: str | The help text depending on the current path.
    """
    config = SiteConfiguration.get_solo()
    kwargs["help_text"] = config.get_help_text(request)
    return {**kwargs, "request": request}


@register.simple_tag(takes_context=True)
def display_search(context):
    """
    Determine if search should be displayed based on configuration and user status.

    Logic:
    1. Search must be globally enabled (SiteConfiguration.search_enabled)
    2. For authenticated users: CMS products app must exist
    3. For anonymous users: search must not be hidden from them
       (SiteConfiguration.hide_search_from_anonymous_users)

    Returns:
        bool: True if search should be displayed
    """
    request = context.get("request")
    config = SiteConfiguration.get_solo()

    if not config.search_enabled:
        return False

    if request.user.is_authenticated:
        cms_apps = context.get("cms_apps", {})
        return bool(cms_apps.get("products"))

    return not config.hide_search_from_anonymous_users
