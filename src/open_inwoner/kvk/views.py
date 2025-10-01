from typing import cast

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from furl import furl

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.accounts.models import User
from open_inwoner.utils.url import get_next_url_from
from open_inwoner.utils.views import LogMixin

from .client import KvKClient
from .exceptions import KVKAPIException
from .forms import CompanyBranchChoiceForm


class CompanyBranchChoiceView(LogMixin, FormView):
    """Choose the branch ("vestiging") of a company"""

    template_name = "pages/kvk/branches.html"
    form_class = CompanyBranchChoiceForm

    def get_form_kwargs(self):
        """
        The `company_branches` data is needed several times at different stages of the
        form view. We inject the value into the form instance instead of retrieving it
        through `get_context_data` in order to avoid multiple IO calls.
        """
        kwargs = super().get_form_kwargs()

        kvk_client = KvKClient()

        try:
            company_branches = kvk_client.get_all_company_branches(
                kvk=self.request.user.kvk
            )
        except KVKAPIException:
            messages.error(
                request=self.request,
                message=_(
                    "We are temporarily unable to show your branches, please try again at a later point."
                ),
            )
            company_branches = []

        # create pseudo-branch representing the company as a whole (the "rechtspersoon").
        # technically, the compnay as a legal entity is represented as "rechtspersoon",
        # but this is not always included in query results
        rechtspersoon_entry = {
            "vestigingsnummer": "",
            "naam": company_branches[0].get("naam", "") if company_branches else "",
        }
        company_branches.insert(0, rechtspersoon_entry)

        kwargs["company_branches"] = company_branches

        return kwargs

    def get_redirect(self):
        if next := get_next_url_from(self.request, default=""):
            redirect = furl(next)
            redirect.args.update(self.request.GET)
        elif self.request.user.require_necessary_fields():
            redirect = furl(reverse("profile:registration_necessary"))
            redirect.args.update(self.request.GET)
        else:
            redirect = furl(reverse("pages-root"))
        return redirect.url

    def check_permissions(self, request):
        user = cast(User, request.user)
        context = EHerkenningSessionContext(request)

        # Only eHerkenning users can potentially switch to a vestiging
        try:
            context.assert_valid_eherkenning_user(user)
        except ValueError:
            return HttpResponse(_("Unauthorized"), status=401)

        if context.is_branch_restricted():
            return HttpResponse(
                _("Your eHerkenning account cannot access other branches."),
                status=401,
            )

    def dispatch(self, request, *args, **kwargs):
        if bad_auth_response := self.check_permissions(request):
            return bad_auth_response

        # Assume we can access this page, we mark the branch selection is done if the
        # page is visited
        eherkenning_context = EHerkenningSessionContext(request)
        eherkenning_context.mark_initial_branch_selection_done()

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        redirect = self.get_redirect()
        context = super().get_context_data()

        form = context["form"]

        # check that there are company branches besides our artifical "rechtspersoon_entry"
        vestigingen = form.company_branches[1:]
        if not vestigingen or not any(v.get("vestigingsnummer") for v in vestigingen):
            self.log_system_action(
                f"List of company branches for KVK number {request.user.kvk} contains "
                "no branch with vestigingsnummer"
            )

            return HttpResponseRedirect(redirect)

        context["company_branches"] = form.company_branches

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        redirect = self.get_redirect()
        context = self.get_context_data()

        form = context["form"]

        if not form.is_valid():
            context["company_branches"] = form.company_branches
            # Directly calling `super().form_invalid(form)` would override the error
            return self.render_to_response(context)

        # Empty string for branch_number is interpreted as "interact as the
        # rechtspersoon, not as any specific branch"
        branch_number = form.cleaned_data["branch_number"]

        # Change the user
        eherkenning_context = EHerkenningSessionContext(request)
        eherkenning_context.change_authenticated_user(
            kvk=request.user.kvk,
            vestiging=branch_number or None,
        )

        self.log_user_action(
            request.user,
            (
                "Selected branch %s of rechtspersoon %s"
                % (branch_number, request.user.kvk)
                if branch_number
                else "Selected rechtspersoon %s" % request.user.kvk
            ),
        )

        return HttpResponseRedirect(redirect)
