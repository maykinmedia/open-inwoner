from django import template

register = template.Library()


@register.filter("startswith")
def startswith(text, starts):
    """
    check if a string startswith a value

    Usage:
        {{ "this is a string"|startswith:"thi" }}

    Variables:
        + text: string | the text that will be matched on.
        + value: string | what the text should start with.
    """
    if isinstance(text, str):
        return text.startswith(starts)
    return False
