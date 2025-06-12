from django.http import HttpRequest

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext


def set_branch_selection_state(request: HttpRequest):
    context = {}
    try:
        ctx = EHerkenningSessionContext(request)
        context["is_branch_restricted"] = ctx.is_branch_restricted
        context["is_initial_Branch_selection_done"] = (
            ctx.is_initial_branch_selection_done
        )
        context["is_eherkenning_session"] = True
    except ValueError:
        context["is_eherkenning_session"] = False

    return context
