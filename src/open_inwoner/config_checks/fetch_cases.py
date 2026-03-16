import requests
from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.utils.api import get_json_response


class FetchCasesConfigCheck:
    identifier = "fetch_cases_for_bsn"
    verbose_name = "Fetch cases for BSN"

    def __init__(self, api_group, bsn):
        self.api_group = api_group
        self.bsn = bsn

    def __call__(self):
        from open_inwoner.openzaak.clients import build_zgw_client_from_service

        client = build_zgw_client_from_service(
            self.api_group.zrc_service,
            use_openzaak_120_params=self.api_group.fetch_eherkenning_zaken_with_openzaak_120_params,
            fetch_rollen_with_betrokkene_type=self.api_group.fetch_rollen_with_betrokkene_type,
        )

        try:
            response = client.get(
                "zaken",
                params={
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.bsn,
                    "maximaleVertrouwelijkheidaanduiding": "openbaar",
                },
                headers={
                    "Accept-Crs": "EPSG:4326",
                    "Content-Crs": "EPSG:4326",
                },
            )

            if not response.ok:
                try:
                    error = response.json()
                except ValueError:
                    error = {"detail": response.text}

                return GenericHealthCheckResult(
                    success=False,
                    identifier=self.identifier,
                    verbose_name=self.verbose_name,
                    message=f"ZGW API returned HTTP {response.status_code}: {error.get('detail')}",
                    extra=error,
                )

            data = get_json_response(response)

            cases = data.get("results", [])

            return GenericHealthCheckResult(
                success=True,
                identifier=self.identifier,
                verbose_name=self.verbose_name,
                message=f"Fetched {len(cases)} cases for user",
                extra={"cases_found": len(cases)},
            )

        except requests.exceptions.RequestException as exc:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.verbose_name,
                message=f"Connection error: {exc}",
                extra={},
            )
