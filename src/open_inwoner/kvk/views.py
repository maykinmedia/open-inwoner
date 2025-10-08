from typing import Any, cast

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import escape
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

    @staticmethod
    def format_address(address_data: dict[str, Any]) -> str:
        """
        Format address data into a human-readable string.

        Handles both combined straatHuisnummer field and separate
        straatnaam/huisnummer/huisnummerToevoeging fields.

        Args:
            address_data: Dictionary containing address fields from KVK API

        Returns:
            Formatted address string, or empty string if no address data
        """
        if not address_data:
            return ""

        # Check for combined street+house number field first
        if address_data.get("straatHuisnummer"):
            return address_data["straatHuisnummer"]

        # Build address from separate components
        address_parts = []
        if address_data.get("straatnaam"):
            address_parts.append(address_data["straatnaam"])
        if address_data.get("huisnummer"):
            address_parts.append(str(address_data["huisnummer"]))
        if address_data.get("huisnummerToevoeging"):
            address_parts.append(address_data["huisnummerToevoeging"])

        return " ".join(address_parts)

    def get_vestigingen_combobox_data(
        self, branches: list[dict], selected_id: str | None = None
    ) -> dict:
        """
        Convert Django branch data to React-compatible JSON format for the KVKBranchSelector component.
        This includes only the branch data - translations are handled by react-intl.

        IMPORTANT: The data flow works as follows:
        1. Django creates this JSON data with branch info
        2. HTML template embeds this JSON in a <script> tag
        3. React KVKBranchSelectorModule reads this JSON and renders the dropdown
        4. User selects a branch in React UI
        5. React creates hidden <input name="branch_number"> with selected branch ID
        6. Form submission sends branch_number back to Django
        7. Django view reads request.POST['branch_number'] to get user's choice

        Args:
            branches: List of branch dictionaries from KVK API
            selected_id: Currently selected vestigingsnummer (or "rechtspersoon")

        Returns:
            Safe JSON string ready to embed in HTML template
        """

        items = []
        for branch in branches:
            # Handle the "entire company" case (empty vestigingsnummer)
            # CRITICAL: This branch_id becomes the value sent back to Django as 'branch_number'
            # Use "rechtspersoon" as default for clarity (Dutch legal entity term)
            # Note: Using 'or' to handle both missing AND empty string values
            branch_id = branch.get("vestigingsnummer") or "rechtspersoon"

            # Build structured additional info for multi-line display in React dropdown
            vestiging_info = ""
            rechtspersoon_info = ""

            # Check branch type once and build appropriate info
            if branch_id == "rechtspersoon":
                # Show "(Rechtspersoon)" as separate line for entire company option
                rechtspersoon_info = "Selecteer de rechtspersoon (geen vestiging)"
            else:
                vestiging_info = f"Vestiging: {branch['vestigingsnummer']}"
                if branch.get("type") == "hoofdvestiging":
                    vestiging_info += " (Hoofdvestiging)"

            # Add address information to help users identify the correct branch
            adres = branch.get("adres", {}).get("binnenlandsAdres", {})
            address_info = self.format_address(adres)

            # Get city information
            city_info = adres.get("plaats", "")

            # Properly escape all string values to prevent Cross-Site Scripting attacks
            # React will display these values in the interactive dropdown
            items.append(
                {
                    "id": escape(
                        str(branch_id)
                    ),  # Used as form value for branch_number field
                    "label": escape(str(branch.get("naam", ""))),
                    "vestigingInfo": escape(vestiging_info),
                    "rechtspersoonInfo": escape(rechtspersoon_info),
                    "addressInfo": escape(address_info),
                    "cityInfo": escape(city_info),
                    "vestigingsnummer": escape(str(branch.get("vestigingsnummer", ""))),
                    "type": escape(str(branch.get("type", ""))),
                }
            )

        return {
            "items": items,
            "selected_id": escape(
                str(selected_id or "")
            ),  # Pre-selected branch for React component
            # No translations here - handled by react-intl in the React component
        }

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        user = cast(User, self.request.user)

        context["company_branches"] = form.company_branches
        context["vestigingen_combobox_data"] = self.get_vestigingen_combobox_data(
            form.company_branches, user.vestiging
        )

        return context

    def get(self, request, *args, **kwargs):
        redirect = self.get_redirect()
        context = self.get_context_data()
        form = context["form"]
        user = cast(User, self.request.user)

        # check that there are company branches besides our artifical "rechtspersoon_entry"
        vestigingen = form.company_branches[1:]
        if not vestigingen or not any(v.get("vestigingsnummer") for v in vestigingen):
            self.log_system_action(
                f"List of company branches for KVK number {user.kvk} contains "
                "no branch with vestigingsnummer"
            )

            return HttpResponseRedirect(redirect)

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        redirect = self.get_redirect()
        context = self.get_context_data()

        form = context["form"]

        if not form.is_valid():
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
