from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from furl import furl

from .client import KvKClient
from .forms import CompanyBranchChoiceForm


class CompanyBranchChoiceView(FormView):
    """Choose the branch ("vestiging") of a company"""

    template_name = "pages/kvk/branches.html"
    form_class = CompanyBranchChoiceForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        kvk_client = KvKClient()

        company_branches = kvk_client.get_all_company_branches(
            kvk=self.request.user.kvk
        )
        form = self.get_form()

        if next := self.request.GET.get("next"):
            redirect = furl(next)
            redirect.args.update(self.request.GET)
        elif self.request.user.require_necessary_fields():
            redirect = furl(reverse("profile:registration_necessary"))
            redirect.args.update(self.request.GET)
        else:
            redirect = furl(reverse("pages-root"))

        context.update(
            company_branches=company_branches,
            form=form,
            redirect=redirect,
        )

        return context

    def get(self, request):
        if not getattr(request.user, "kvk", None):
            return HttpResponse(_("Unauthorized"), status=401)

        context = self.get_context_data()

        redirect = context["redirect"]
        company_branches = context["company_branches"]

        if not company_branches:
            return HttpResponseRedirect(redirect.url)

        if len(company_branches) == 1:
            request.session["KVK_BRANCH_NUMBER"] = (
                company_branches[0].get("vestigingsnummer") or request.user.kvk
            )
            request.session.save()
            return HttpResponseRedirect(redirect.url)

        form = context["form"]

        return render(
            request,
            self.template_name,
            {
                "company_branches": company_branches,
                "form": form,
            },
        )

    def post(self, request):
        if not getattr(request.user, "kvk", None):
            return HttpResponse(_("Unauthorized"), status=401)

        form = self.get_form()

        if form.is_valid():
            context = self.get_context_data()
            redirect = context["redirect"]

            cleaned = form.cleaned_data
            branch_number = cleaned["branch_number"]

            request.session["KVK_BRANCH_NUMBER"] = branch_number

            return HttpResponseRedirect(redirect.url)

        return super().form_invalid(form)
