from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from open_inwoner.kvk.branches import KVK_BRANCH_SESSION_VARIABLE

from ..utils.url import get_next_url_from
from .client import KvKClient
from .forms import CompanyBranchChoiceForm


class CompanyBranchChoiceView(FormView):
    """Choose the branch ("vestiging") of a company"""

    # TODO refactor for proper Class Based View usage:
    # - get_context_data() does network IO but is called multiple times (also through super())
    # - get_form() is called multiple times (also through super())
    # - use regular FormView code patterns (should work without get()/post())
    # - move saving to the form's .save() (pass arguments form_kwargs of save()-argument

    template_name = "pages/kvk/branches.html"
    form_class = CompanyBranchChoiceForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        kvk_client = KvKClient()

        company_branches = kvk_client.get_all_company_branches(
            kvk=self.request.user.kvk
        )
        form = self.get_form()

        redirect = get_next_url_from(self.request, default=reverse("pages-root"))
        # if next := self.request.GET.get("next"):
        #     redirect = furl(next)
        #     redirect.args.update(self.request.GET)
        # elif self.request.user.require_necessary_fields():
        #     redirect = furl(reverse("profile:registration_necessary"))
        #     redirect.args.update(self.request.GET)
        # else:
        #     redirect = furl(reverse("pages-root"))

        # create pseudo-branch representing the company as a whole
        master_branch = {
            "vestigingsnummer": "",
            "naam": company_branches[0].get("naam", "") if company_branches else "",
        }
        company_branches.insert(0, master_branch)

        context.update(
            company_branches=company_branches,
            form=form,
            redirect=redirect,
        )

        return context

    def get(self, request):
        if not getattr(request.user, "kvk", None):
            return HttpResponse(_("Unauthorized"), status=401)

        # TODO regular FormView does this
        context = self.get_context_data()

        redirect = context["redirect"]
        company_branches_with_master = context["company_branches"]
        # Exclude the "master" branch from these checks, since we always insert this
        company_branches = company_branches_with_master[1:]

        if not company_branches:
            request.session[KVK_BRANCH_SESSION_VARIABLE] = None
            request.session.save()
            return HttpResponseRedirect(redirect)

        if len(company_branches) == 1:
            request.session[KVK_BRANCH_SESSION_VARIABLE] = None
            request.session.save()
            return HttpResponseRedirect(redirect)

        form = context["form"]

        # TODO regular FormView does this
        return render(
            request,
            self.template_name,
            {
                "company_branches": company_branches_with_master,
                "form": form,
            },
        )

    def post(self, request):
        if not getattr(request.user, "kvk", None):
            return HttpResponse(_("Unauthorized"), status=401)

        # TODO this is also called from get_context_data()
        form = self.get_form()

        if form.is_valid():
            context = self.get_context_data()
            redirect = context["redirect"]

            cleaned = form.cleaned_data
            branch_number = cleaned["branch_number"]

            if branch_number and not any(
                branch.get("vestigingsnummer") == branch_number
                for branch in context["company_branches"]
            ):
                form.add_error(
                    "branch_number",
                    _("Invalid branch number for the current KvK number"),
                )
                context["form"] = form
                # Directly calling `super().form_invalid(form)` would override the error
                return self.render_to_response(context)

            request.session[KVK_BRANCH_SESSION_VARIABLE] = branch_number

            return HttpResponseRedirect(redirect)

        # TODO this calls get_context_data() again
        return super().form_invalid(form)
