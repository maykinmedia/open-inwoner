from typing import Any, Optional, TypedDict

from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext as _

from maykin_config_checks import GenericConfigCheckResult
from maykin_config_checks.permissions import IsSuperUser
from maykin_config_checks.protocols import InteractiveConfigCheck
from open_inwoner.kvk.client import KvKClient
from open_inwoner.kvk.exceptions import KVKAPIException
from open_inwoner.kvk.models import KvKConfig
from open_inwoner.utils.logentry import system_action, user_action


class FetchCompanyForm(forms.Form):
    kvk_number = forms.CharField(max_length=8, label=_("KvK number"))


class FetchCompanyCheckParams(TypedDict):
    kvk_number: str


class FetchCompanyCheck(
    InteractiveConfigCheck[
        FetchCompanyCheckParams,
        KvKConfig,
    ]
):
    identifier = "fetch_company"
    label = _("Fetch company for KvK number")
    form_class = FetchCompanyForm

    required_permissions = (IsSuperUser(),)

    @classmethod
    def get_form_kwargs(
        cls,
        instance: Optional[KvKConfig] = None,
    ) -> dict[str, Any]:
        return {}

    def get_target_object(
        self,
        data: FetchCompanyCheckParams,
        instance: Optional[KvKConfig],
    ) -> Optional[KvKConfig]:
        return instance

    def run(
        self,
        data: FetchCompanyCheckParams,
        instance: Optional[KvKConfig] = None,
        request: Optional[HttpRequest] = None,
    ) -> GenericConfigCheckResult:
        kvk_number = data["kvk_number"]
        log_message = f"fetch company check run for kvk number {kvk_number}"

        if request:
            user_action(request, request.user, log_message)
        else:
            system_action(log_message)

        if not kvk_number.isdigit() or len(kvk_number) != 8:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Invalid KvK number format (must be 8 digits)"),
                extra={},
            )

        try:
            client = KvKClient(instance)

            # Mirrors the real call sequence: basisprofiel + RSIN on every
            # eHerkenning login (accounts/signals.py), branches on the branch
            # switcher page (kvk/views.py), and, for whichever branch that
            # search turns up, its vestigingsprofiel (also signals.py, for
            # branch-restricted users).
            basisprofiel = client.get_basisprofiel(kvk_number)
            rsin = client.retrieve_rsin_with_kvk(kvk_number)
            branches = client.get_all_company_branches(kvk_number)

            vestigingsprofiel = None
            if branches and (vestigingsnummer := branches[0].get("vestigingsnummer")):
                vestigingsprofiel = client.get_vestigingsprofiel(vestigingsnummer)
        except KVKAPIException as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Failed to connect to KvK API"),
                extra={"error": exc.message, "type": type(exc).__name__},
            )
        except Exception as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Unexpected error while fetching company"),
                extra={"exception": str(exc), "type": type(exc).__name__},
            )

        if not basisprofiel:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("No company found for this KvK number"),
                extra={},
            )

        return GenericConfigCheckResult(
            success=True,
            identifier=self.identifier,
            verbose_name=self.label,
            message=_("Company data returned"),
            extra={
                "basisprofiel": basisprofiel,
                "rsin": rsin,
                "branches": branches,
                "vestigingsprofiel": vestigingsprofiel,
            },
        )
