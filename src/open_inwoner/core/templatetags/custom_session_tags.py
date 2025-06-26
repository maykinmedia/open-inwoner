from typing import cast

from django import template
from django.http import HttpRequest

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext

register = template.Library()


@register.simple_tag(takes_context=True)
def session_is_branch_restricted(context) -> bool:
    request = cast(HttpRequest, context["request"])
    eherkenning_ctx = EHerkenningSessionContext(request)
    return eherkenning_ctx.is_branch_restricted()
