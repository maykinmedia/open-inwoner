from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.openzaak.clients import build_zgw_client_from_service
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.utils.api import get_json_response

from .forms import FetchCasesConfigCheckParams
from .permissions import HasModelWrite


class FetchCasesCheck:
    identifier = "fetch_cases"
    label = "Fetch cases for BSN"
    form_class = FetchCasesConfigCheckParams
    required_permissions = (HasModelWrite(ZGWApiGroupConfig),)

    @classmethod
    def get_form_kwargs(cls, obj):
        initial = {}

        if obj:
            initial["api_group"] = obj

        return {"initial": initial}

    def get_target_object(self, form, obj):
        return form.cleaned_data.get("api_group") or obj

    def run(self, form, obj=None) -> GenericHealthCheckResult:
        bsn = form.cleaned_data["bsn"]

        from zgw_consumers.models import Service

        from open_inwoner.openzaak.models import ZGWApiGroupConfig

        if isinstance(obj, ZGWApiGroupConfig):
            api_group = obj
            service = obj.zrc_service

        elif isinstance(obj, Service):
            service = obj
            api_group = ZGWApiGroupConfig.objects.filter(zrc_service=service).first()

        else:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=f"Invalid object type: {type(obj).__name__}",
            )

        if not service:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message="No ZRC Service is configured for this API group.",
            )

        client = build_zgw_client_from_service(
            service,
            use_openzaak_120_params=(
                api_group.fetch_eherkenning_zaken_with_openzaak_120_params
                if api_group
                else False
            ),
            fetch_rollen_with_betrokkene_type=(
                api_group.fetch_rollen_with_betrokkene_type if api_group else False
            ),
        )
        try:
            response = client.get(
                "zaken",
                params={
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": bsn,
                    "maximaleVertrouwelijkheidaanduiding": "openbaar",
                },
                headers={"Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"},
            )

            if not response.ok:
                return GenericHealthCheckResult(
                    success=False,
                    identifier=self.identifier,
                    verbose_name=self.label,
                    message=f"ZGW API returned HTTP {response.status_code}",
                    extra={"response": response.text},
                )

            data = get_json_response(response)
            cases = data.get("results", [])
            return GenericHealthCheckResult(
                success=True,
                identifier=self.identifier,
                verbose_name=self.label,
                message=f"Fetched {len(cases)} cases",
                extra={"cases_found": len(cases)},
            )

        except Exception as exc:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=str(exc),
                extra={"exception": repr(exc)},
            )
