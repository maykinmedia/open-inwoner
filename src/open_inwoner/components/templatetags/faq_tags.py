from django import template
from django.db.models import QuerySet
from django.utils.translation import gettext as _

register = template.Library()


@register.inclusion_tag("components/Faq/Faq.html")
def faq(questions: QuerySet, **kwargs):
    """
    Shows a list of questions, with collapsible answers.

    Usage:
        {% faq questions=Category.question_set.all %}
        {% faq questions=Category.question_set.all title=_('FAQ') %}

    Variables:
        + questions: array | this is the list of file that need to be rendered.
        - title: string | The title that should be used. Leave empty for no title.
    """
    return {
        **kwargs,
        "questions": questions,
        "title": kwargs.get("title", _("Veelgestelde vragen")),
    }
