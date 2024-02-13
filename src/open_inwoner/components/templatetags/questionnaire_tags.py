from django import template
from django.db.models import QuerySet

register = template.Library()


@register.inclusion_tag("components/Questionnaire/Questionnaire.html")
def questionnaire(root_nodes: QuerySet, **kwargs):
    """
    Shows a list with the root nodes of a questionnaire.

    Usage:
        {% questionnaire root_nodes=QuestionnaireStep.get_root_nodes %}

    Variables:
        + root_nodes: QuestionnaireStep[] | this is the list of QuestionnaireStep root nodes that need to be rendered.
    """
    return {**kwargs, "root_nodes": root_nodes}
