from typing import Any, Optional, TypedDict

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.translation import gettext as _

from log_outgoing_requests.models import OutgoingRequestsLogConfig
from pydantic import ValidationError

from maykin_config_checks import GenericConfigCheckResult
from maykin_config_checks.permissions import IsSuperUser
from maykin_config_checks.protocols import InteractiveConfigCheck
from maykin_config_checks.registry import registry
from open_inwoner.haalcentraal.clients import BRPClient
from open_inwoner.haalcentraal.exceptions import BRPAPIError
from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.utils.logentry import system_action, user_action


class FetchBRPForm(forms.Form):
    bsn = forms.CharField(max_length=9, label="BSN")


class FetchBRPCheckParams(TypedDict):
    bsn: str


class FetchBRPCheck(
    InteractiveConfigCheck[
        FetchBRPCheckParams,
        HaalCentraalConfig,
    ]
):
    identifier = "fetch_brp"
    label = _("Fetch BRP data for BSN")
    form_class = FetchBRPForm

    required_permissions = (IsSuperUser(),)

    @classmethod
    def get_form_kwargs(
        cls,
        instance: Optional[HaalCentraalConfig] = None,
    ) -> dict[str, Any]:
        return {}

    def run(
        self,
        data: FetchBRPCheckParams,
        instance: Optional[HaalCentraalConfig] = None,
        request: Optional[HttpRequest] = None,
    ) -> GenericConfigCheckResult:
        bsn = data["bsn"]
        masked_bsn = f"{bsn[:3]}******"
        log_message = f"fetch BRP check run for bsn {masked_bsn}"

        if request:
            user_action(request, request.user, log_message)
        else:
            system_action(log_message)

        if OutgoingRequestsLogConfig.get_solo().save_body_enabled:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_(
                    "This check cannot be run while outgoing request log bodies "
                    "are being saved, since it exposes personal data (BSN and "
                    "BRP data) in the outgoing request logs. Disable 'Save "
                    "request + response body' in the outgoing request log "
                    "configuration before running this check."
                ),
                extra={},
            )

        if not bsn.isdigit() or len(bsn) != 9:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Invalid BSN format (must be 9 digits)"),
                extra={},
            )

        try:
            client = BRPClient.from_config()
        except ImproperlyConfigured as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Haal Centraal is not configured"),
                extra={"error": str(exc)},
            )

        try:
            persoon = client.fetch_brp_data_for_bsn(bsn)
        except ValidationError as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Connected, but the response data failed validation"),
                extra={"error": str(exc), "version": client.version},
            )
        except BRPAPIError as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Failed to connect to the BRP API"),
                extra={"error": str(exc), "type": type(exc).__name__},
            )
        except Exception as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Unexpected error while fetching BRP data"),
                extra={"exception": str(exc), "type": type(exc).__name__},
            )

        if persoon is None:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("No person found for this BSN"),
                extra={"version": client.version},
            )

        return GenericConfigCheckResult(
            success=True,
            identifier=self.identifier,
            verbose_name=self.label,
            message=_("BRP data retrieved and validated (version %(version)s)")
            % {"version": client.version},
            extra={"version": client.version},
        )


registry.register(FetchBRPCheck)
