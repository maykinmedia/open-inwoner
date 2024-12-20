from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from furl import furl

from open_inwoner.kvk.branches import KVK_BRANCH_SESSION_VARIABLE
from open_inwoner.utils.views import LogMixin

from ..utils.url import get_next_url_from
from .client import KvKClient
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

        company_branches = kvk_client.get_all_company_branches(
            kvk=self.request.user.kvk
        )
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

    def get(self, request, *args, **kwargs):
        if not getattr(request.user, "kvk", None):
            return HttpResponse(_("Unauthorized"), status=401)

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
            request.session[KVK_BRANCH_SESSION_VARIABLE] = None
            request.session.save()
            return HttpResponseRedirect(redirect)

        context["company_branches"] = form.company_branches

        return render(request, self.template_name, context)

    def post(self, request):
        if not getattr(request.user, "kvk", None):
            return HttpResponse(_("Unauthorized"), status=401)

        redirect = self.get_redirect()
        context = self.get_context_data()

        form = context["form"]

        if not form.is_valid():
            context["company_branches"] = form.company_branches
            # Directly calling `super().form_invalid(form)` would override the error
            return self.render_to_response(context)

        # empty string for KVK_BRANCH_SESSION_VARIABLE is interpreted as
        # "interact as the rechtspersoon, not as any specific branch"
        request.session[KVK_BRANCH_SESSION_VARIABLE] = request.POST["branch_number"]

        return HttpResponseRedirect(redirect)
