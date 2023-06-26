from django import template
from django.db.models import QuerySet

register = template.Library()


@register.inclusion_tag("components/TabPanel/TabPanel.html")
def render_tabs_panel(get_tabs: QuerySet, content, title, **kwargs):
    """
    Renders a tabbed navigation where content-panels are shown when clicking the tab title.

    Usages:
        {% load tabs_panel_tags %}
        {% render_tabs_panel  title=title content=content get_tabs=get_tabs %}

    Variables:
        + get_tabs: array | this is the list of tabs that need to be rendered.
        + id: string | The id of the tab list-item.
        + title: string | The clickable or tabbable tab title.
        + content: string | The panel content that is displayed when the tab title is clicked.
    """
    get_tabs = [
        {
            "id": "tab1",
            "title": "Uitkeringsspecificaties",
            "content": "Selecteer de maand die u wilt downloaden. Let op: de huidige maand is pas vanaf de 25ste zichtbaar. Deze uitkeringsspecificatie is een momentopname van de aan u uitbetaalde uitkering. Aan deze specificatie kunt u geen rechten ontlenen.",
        },
        {
            "id": "tab2",
            "title": "Jaaropgaven",
            "content": "Here is the content of Tab 2.",
        },
        # Add more tabs if needed
    ]
    return {
        **kwargs,
        "get_tabs": get_tabs,
        "content": content,
        "title": title,
    }
