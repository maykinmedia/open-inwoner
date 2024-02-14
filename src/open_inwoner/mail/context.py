from django.urls import reverse

from open_inwoner.cms.utils.page_display import profile_page_is_published
from open_inwoner.configurations.models import SiteConfiguration


def mail_context():
    """
    Context added to mail editor templates
    """
    context = {}
    config = SiteConfiguration.get_solo()
    context["logo"] = config.email_logo
    context["theming"] = {
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "accent_color": config.accent_color,
        "primary_font_color": config.primary_font_color,
        "secondary_font_color": config.secondary_font_color,
        "accent_font_color": config.accent_font_color,
    }
    context["login_page"] = reverse("login")

    if profile_page_is_published():
        context["profile_notifications"] = reverse("profile:notifications")
        context["profile_page"] = reverse("profile:detail")
    else:
        # empty urls to homepage
        context["profile_notifications"] = ""
        context["profile_page"] = ""

    # if a contact page exists it is a FlatPage
    context["contactpage"] = "????"

    return context
