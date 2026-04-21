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
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig
from open_inwoner.utils.logentry import system_action, user_action


class FetchCasesForm(forms.Form):
    api_group = forms.ModelChoiceField(
        queryset=ZGWApiGroupConfig.objects.all(),
        required=False,
        help_text=_("Select API group (required if not running from object page)"),
    )
    bsn = forms.CharField(max_length=9, label="BSN")


class FetchCasesCheckParams(TypedDict):
    api_group: ZGWApiGroupConfig | None
    bsn: str


class FetchCasesCheck(
    InteractiveConfigCheck[
        FetchCasesCheckParams,
        ZGWApiGroupConfig,
    ]
):
    identifier = "fetch_cases"
    label = _("Fetch cases for BSN")
    form_class = FetchCasesForm

    required_permissions = (IsSuperUser(),)

    @classmethod
    def get_form_kwargs(
        cls,
        instance: Optional[ZGWApiGroupConfig] = None,
    ) -> dict[str, Any]:
        initial = {}

        if instance:
            initial["api_group"] = instance

        return {"initial": initial}

    def get_target_object(
        self,
        data: FetchCasesCheckParams,
        instance: Optional[ZGWApiGroupConfig],
    ) -> Optional[ZGWApiGroupConfig]:
        return data.get("api_group") or instance

    def run(
        self,
        data: FetchCasesCheckParams,
        instance: Optional[ZGWApiGroupConfig] = None,
        request: Optional[HttpRequest] = None,
    ) -> GenericConfigCheckResult:
        bsn = data["bsn"]
        masked_bsn = f"{bsn[:3]}******"
        log_message = f"fetch cases check run for bsn {masked_bsn}"

        if request:
            user_action(
                request,
                request.user,
                log_message,
            )
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

        obj = self.get_target_object(data, instance)

        if not obj:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("No API group selected"),
                extra={
                    "hint": _("Select an API group or run this from an object page")
                },
            )

        try:
            client = obj.zaken_client
            zaken = client.fetch_zaken(user_identification=BSNIdentification(bsn=bsn))
            count = len(zaken)

            config = OpenZaakConfig.get_solo()

            if count == 0:
                hints = []
                base_url = getattr(client, "base_url", "") or ""

                if config.limit_user_visible_cases_to_role:
                    hints.append(
                        _("Filtered by role '%(role)s'")
                        % {"role": config.limit_user_visible_cases_to_role}
                    )

                if config.zaak_max_confidentiality != "openbaar":
                    hints.append(
                        _("Filtered by confidentiality ≤ '%(level)s'")
                        % {"level": config.zaak_max_confidentiality}
                    )

                if not hints:
                    hints.append(
                        _("No filtering detected — likely no data exists for this BSN")
                    )

                return GenericConfigCheckResult(
                    success=False,
                    identifier=self.identifier,
                    verbose_name=self.label,
                    message=_("No cases returned"),
                    extra={
                        "diagnosis": _(
                            "No data returned by API (not a connectivity error)"
                        ),
                        "count": 0,
                        "bsn": masked_bsn,
                        "service": str(obj.zrc_service),
                        "client": {
                            "base_url": base_url,
                        },
                        "query": {
                            "bsn_param": "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn",
                            "max_confidentiality": config.zaak_max_confidentiality,
                        },
                        "openzaak_config": {
                            "max_confidentiality": config.zaak_max_confidentiality,
                            "limit_role": config.limit_user_visible_cases_to_role
                            or None,
                        },
                        "hints": hints,
                    },
                )

            return GenericConfigCheckResult(
                success=True,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Fetched %(count)s cases for BSN %(bsn)s")
                % {"count": count, "bsn": bsn},
                extra={
                    "count": count,
                    "sample": getattr(zaken[0], "identificatie", None),
                    "service": str(obj.zrc_service),
                    "base_url": getattr(client, "base_url", None),
                    "config": {
                        "use_openzaak_120_params": getattr(
                            obj,
                            "fetch_eherkenning_zaken_with_openzaak_120_params",
                            None,
                        ),
                        "fetch_rollen_with_betrokkene_type": getattr(
                            obj,
                            "fetch_rollen_with_betrokkene_type",
                            None,
                        ),
                    },
                },
            )

        except RequestException as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Failed to connect to Zaken API"),
                extra={
                    "error": str(exc),
                    "type": type(exc).__name__,
                    "base_url": getattr(client, "base_url", None),
                },
            )

        except Exception as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Unexpected error while fetching cases"),
                extra={
                    "exception": str(exc),
                    "type": type(exc).__name__,
                },
            )


registry.register(FetchCasesCheck)
