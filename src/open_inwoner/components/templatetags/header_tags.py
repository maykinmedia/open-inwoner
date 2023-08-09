from django import template
from django.db.models import Q

from cms.models import Page

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

    # help texts for cms pages with extension
    cms_pages = Page.objects.filter(
        Q(publisher_is_draft=False) and Q(commonextension__isnull=False)
    ).select_related("commonextension")

    for page in cms_pages:
        if page.application_namespace in (
            "collaborate",
            "home",
            "inbox",
            "products",
            "profile",
            "ssd",
        ):
            kwargs["help_text"] = page.commonextension.help_text
        elif page.get_absolute_url() in ("", "/"):
            kwargs["help_text"] = page.commonextension.help_text

    # help texts for cms pages without extension
    cms_pages = Page.objects.filter(
        Q(publisher_is_draft=False) and Q(commonextension__isnull=True)
    )
    for page in cms_pages:
        kwargs["help_text"] = SiteConfiguration.get_solo().get_help_text(request)

    return {**kwargs, "request": request}
