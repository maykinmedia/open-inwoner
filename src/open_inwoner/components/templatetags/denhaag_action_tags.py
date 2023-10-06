from django import template

register = template.Library()


@register.inclusion_tag("components/DenhaagAction/DenhaagAction.html")
def denhaag_action(title, date, link, **kwargs):
    kwargs["title"] = title
    kwargs["date"] = date
    kwargs["link"] = link
    return kwargs
