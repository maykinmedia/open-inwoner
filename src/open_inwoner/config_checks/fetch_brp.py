import requests
from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.haalcentraal.utils import get_brp_api


class FetchBRPConfigCheck:
    identifier = "fetch_brp_for_bsn"
    verbose_name = "Fetch BRP data for BSN"

    def __init__(self, bsn: str):
        self.bsn = bsn

    def __call__(self):
        try:
            api = get_brp_api()
            version = getattr(api, "version", "unknown")

            response = api.fetch_brp(self.bsn)

            persons = [] if response is None else [response]
            count = len(persons)
            message = (
                f"BRP API OK (v{version}) - "
                f"{count} person{'s' if count != 1 else ''} found"
            )
            return GenericHealthCheckResult(
                success=True,
                identifier=self.identifier,
                verbose_name=self.verbose_name,
                message=message,
                extra={
                    "version": version,
                    "status_code": 200,
                    "persons_found": len(persons),
                    "has_data": bool(persons),
                },
            )

        except requests.exceptions.RequestException as exc:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.verbose_name,
                message=f"Connection error: {exc}",
                extra={},
            )

        except Exception as exc:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.verbose_name,
                message=f"BRP request failed: {exc}",
                extra={"exception": repr(exc)},
            )
