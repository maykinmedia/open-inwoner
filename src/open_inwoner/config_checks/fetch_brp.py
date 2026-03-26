from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.haalcentraal.utils import get_brp_api

from .forms import FetchBRPConfigCheckParams


class FetchBRPCheck:
    identifier = "fetch_brp"
    label = "Fetch BRP data for BSN"
    form_class = FetchBRPConfigCheckParams

    def __init__(self, form: FetchBRPConfigCheckParams):
        self.form = form

    def run(self, obj) -> GenericHealthCheckResult:
        bsn = self.form.cleaned_data["bsn"]

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
