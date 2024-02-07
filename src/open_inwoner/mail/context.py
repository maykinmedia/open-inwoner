from open_inwoner.configurations.models import SiteConfiguration


def mail_context():
    """
    Context added to mail editor templates
    """
    context = {}
    config = SiteConfiguration.get_solo()
    context["logo"] = config.logo
    context["footer_logo"] = config.footer_logo
    context["theming"] = {
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "accent_color": config.accent_color,
        "primary_font_color": config.primary_font_color,
        "secondary_font_color": config.secondary_font_color,
        "accent_font_color": config.accent_font_color,
    }
    return context
