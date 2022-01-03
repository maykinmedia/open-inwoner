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


@register.simple_tag(takes_context=True)
def create_button_classes(context):
    classnames = "button"

    if context.get("icon"):
        if not context.get("text"):
            classnames += " button--textless"
        classnames += " button--icon"

    icon_position = context.get("icon_position")
    if icon_position:
        classnames += f" button--icon-{icon_position}"

    size = context.get("size")
    if size:
        classnames += f" button--{size}"

    if context.get("open"):
        classnames += " button--open"

    if context.get("bordered"):
        classnames += " button--bordered"

    if context.get("primary"):
        classnames += " button--primary"

    if context.get("secondary"):
        classnames += " button--secondary"

    if context.get("transparent"):
        classnames += " button--transparent"

    return classnames
