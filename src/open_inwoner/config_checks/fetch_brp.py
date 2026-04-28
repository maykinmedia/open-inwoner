from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.haalcentraal.utils import get_brp_api

from .forms import FetchBRPConfigCheckParams
from .permissions import IsSuperUser


class FetchBRPCheck:
    identifier = "fetch_brp"
    label = "Fetch BRP for BSN"
    form_class = FetchBRPConfigCheckParams
    required_permissions = (IsSuperUser(),)

    @classmethod
    def get_form_kwargs(cls, obj):
        return {}

    def run(
        self,
        form: FetchBRPConfigCheckParams,
        obj=None,
    ) -> GenericHealthCheckResult:
        bsn = form.cleaned_data["bsn"]

        try:
            api = get_brp_api()
            version = getattr(api, "version", "unknown")

            response = api.fetch_brp(bsn)

            persons = [] if response is None else [response]

            return GenericHealthCheckResult(
                success=True,
                identifier=self.identifier,
                verbose_name=self.label,
                message=f"BRP API OK (v{version}) - {len(persons)} found",
                extra={
                    "version": version,
                    "persons_found": len(persons),
                },
            )

        except Exception as exc:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=str(exc),
                extra={"exception": repr(exc)},
            )
