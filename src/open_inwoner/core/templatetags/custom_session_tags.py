from django import template

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext

register = template.Library()


@register.simple_tag(takes_context=True)
def session_is_branch_restricted(context) -> bool:
    eherkenning_ctx = EHerkenningSessionContext(context["request"])
    return eherkenning_ctx.is_branch_restricted()
