from collections import Counter
from typing import Any, Optional, TypedDict

from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext as _

from requests.exceptions import RequestException

from maykin_config_checks import GenericConfigCheckResult
from maykin_config_checks.permissions import IsSuperUser
from maykin_config_checks.protocols import InteractiveConfigCheck
from maykin_config_checks.registry import registry
from open_inwoner.accounts.user_identification import BSNIdentification
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import ZGWService
from open_inwoner.utils.logentry import system_action, user_action


class FetchCasesForm(forms.Form):
    bsn = forms.CharField(max_length=9, label="BSN")


class FetchCasesCheckParams(TypedDict):
    bsn: str


class FetchCasesCheck(
    InteractiveConfigCheck[
        FetchCasesCheckParams,
        OpenZaakConfig,
    ]
):
    identifier = "fetch_cases"
    label = _("Fetch cases for BSN")
    form_class = FetchCasesForm

    required_permissions = (IsSuperUser(),)

    @classmethod
    def get_form_kwargs(
        cls,
        instance: Optional[OpenZaakConfig] = None,
    ) -> dict[str, Any]:
        return {}

    def get_target_object(
        self,
        data: FetchCasesCheckParams,
        instance: Optional[OpenZaakConfig],
    ) -> Optional[OpenZaakConfig]:
        return instance

    def run(
        self,
        data: FetchCasesCheckParams,
        instance: Optional[OpenZaakConfig] = None,
        request: Optional[HttpRequest] = None,
    ) -> GenericConfigCheckResult:
        bsn = data["bsn"]
        masked_bsn = f"{bsn[:3]}******"
        log_message = f"fetch cases check run for bsn {masked_bsn}"

        if request:
            user_action(request, request.user, log_message)
        else:
            system_action(log_message)

        if not bsn.isdigit() or len(bsn) != 9:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Invalid BSN format (must be 9 digits)"),
                extra={},
            )

        try:
            service = ZGWService()
            result = service.get_visible_zaken(BSNIdentification(bsn=bsn))
            count = len(result.zaken)
            skipped = dict(Counter(s.reason.value for s in result.skipped))
            not_visible_count = sum(skipped.values())

            by_group = {}
            for z in result.zaken:
                name = str(z.api_group)
                by_group.setdefault(
                    name,
                    {"total_visible": 0, "total_not_visible": 0, "not_visible": {}},
                )
                by_group[name]["total_visible"] += 1
            for s in result.skipped:
                name = str(s.api_group)
                by_group.setdefault(
                    name,
                    {"total_visible": 0, "total_not_visible": 0, "not_visible": {}},
                )
                by_group[name]["total_not_visible"] += 1
                by_group[name]["not_visible"][s.reason.value] = (
                    by_group[name]["not_visible"].get(s.reason.value, 0) + 1
                )

            extra = {
                "total": count + not_visible_count,
                "total_visible": count,
                "total_not_visible": not_visible_count,
                "not_visible": skipped,
                "by_group": by_group,
            }

            if count == 0:
                return GenericConfigCheckResult(
                    success=False,
                    identifier=self.identifier,
                    verbose_name=self.label,
                    message=_("No visible cases returned"),
                    extra=extra,
                )

            return GenericConfigCheckResult(
                success=True,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("%(count)s cases returned") % {"count": count},
                extra=extra,
            )

        except RequestException as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Failed to connect to Zaken API"),
                extra={"error": str(exc), "type": type(exc).__name__},
            )

        except Exception as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Unexpected error while fetching cases"),
                extra={"exception": str(exc), "type": type(exc).__name__},
            )


registry.register(FetchCasesCheck)
