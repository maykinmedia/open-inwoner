import base64
import concurrent.futures
import logging
import warnings
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, Mapping, Type, TypeAlias, TypeVar

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.functional import SimpleLazyObject

from ape_pie.client import APIClient
from requests import HTTPError, RequestException, Response
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes
from zgw_consumers.client import build_client
from zgw_consumers.concurrent import parallel
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.service import pagination_helper

from open_inwoner.openzaak.api_models import InformatieObject
from open_inwoner.openzaak.exceptions import MultiZgwClientProxyError
from open_inwoner.utils.api import ClientError, get_json_response

from ..utils.decorators import cache as cache_result
from .api_models import (
    InformatieObjectType,
    OpenSubmission,
    OpenTask,
    Resultaat,
    ResultaatType,
    Rol,
    Status,
    StatusType,
    Zaak,
    ZaakInformatieObject,
    ZaakType,
)
from .models import OpenZaakConfig

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}

logger = logging.getLogger(__name__)


class ZgwAPIClient(APIClient):
    """A client for interacting with ZGW services."""

    configured_from: Service

    def __init__(self, *args, **kwargs):
        self.configured_from = kwargs.pop("configured_from")
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"Client {self.__class__.__name__} for {self.base_url}"


class ZakenClient(ZgwAPIClient):
    def fetch_cases(
        self,
        user_bsn: str | None = None,
        user_kvk_or_rsin: str | None = None,
        max_requests: int = 4,
        identificatie: str | None = None,
        vestigingsnummer: str | None = None,
    ):
        if user_bsn and (user_kvk_or_rsin or vestigingsnummer):
            raise ValueError(
                "either `user_bsn` or `user_kvk_or_rsin`/`vestigingsnummer` should be supplied, not both"
            )

        if user_bsn:
            return self.fetch_cases_by_bsn(
                user_bsn, max_requests=max_requests, identificatie=identificatie
            )
        elif user_kvk_or_rsin:
            return self.fetch_cases_by_kvk_or_rsin(
                user_kvk_or_rsin,
                max_requests=max_requests,
                zaak_identificatie=identificatie,
                vestigingsnummer=vestigingsnummer,
            )
        return []

    @cache_result(
        "{self.base_url}:cases:{user_bsn}:{max_requests}:{identificatie}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_cases_by_bsn(
        self,
        user_bsn: str,
        max_requests: int | None = 4,
        identificatie: str | None = None,
    ) -> list[Zaak]:
        """
        retrieve cases for particular user with allowed confidentiality level

        :param:max_requests - used to limit the number of requests to list_zaken resource.
        :param:identificatie - used to filter the cases by a specific identification
        """
        config = OpenZaakConfig.get_solo()

        params = {
            "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": user_bsn,
            "maximaleVertrouwelijkheidaanduiding": config.zaak_max_confidentiality,
        }
        if identificatie:
            params.update({"identificatie": identificatie})

        try:
            response = self.get(
                "zaken",
                params=params,
                headers=CRS_HEADERS,
            )
            data = get_json_response(response)
            all_data = list(
                pagination_helper(
                    self,
                    data,
                    max_requests=max_requests,
                    headers=CRS_HEADERS,
                )
            )
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        cases = factory(Zaak, all_data)

        return cases

    @cache_result(
        "{self.base_url}:cases:{kvk_or_rsin}:{vestigingsnummer}:{max_requests}:{zaak_identificatie}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_cases_by_kvk_or_rsin(
        self,
        kvk_or_rsin: str | None,
        max_requests: int | None = 4,
        zaak_identificatie: str | None = None,
        vestigingsnummer: str | None = None,
    ) -> list[Zaak]:
        """
        retrieve cases for particular company with allowed confidentiality level

        :param max_requests: - used to limit the number of requests to list_zaken resource.
        :param zaak_identificatie: - used to filter the cases by a unique Zaak identification number
        :param vestigingsnummer: - used to filter the cases by a vestigingsnummer
        """
        if not kvk_or_rsin:
            return []

        config = OpenZaakConfig.get_solo()

        params = {
            "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId": kvk_or_rsin,
            "maximaleVertrouwelijkheidaanduiding": config.zaak_max_confidentiality,
        }

        if vestigingsnummer:
            params.update(
                {
                    "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer": vestigingsnummer,
                }
            )

        if zaak_identificatie:
            params.update({"identificatie": zaak_identificatie})

        try:
            response = self.get(
                "zaken",
                params=params,
                headers=CRS_HEADERS,
            )
            data = get_json_response(response)
            all_data = list(
                pagination_helper(
                    self,
                    data,
                    max_requests=max_requests,
                    headers=CRS_HEADERS,
                )
            )
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        cases = factory(Zaak, all_data)

        return cases

    @cache_result(
        "{self.base_url}:single_case:{case_uuid}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_single_case(self, case_uuid: str) -> Zaak | None:
        try:
            response = self.get(f"zaken/{case_uuid}", headers=CRS_HEADERS)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        case = factory(Zaak, data)

        return case

    def fetch_case_by_url_no_cache(self, case_url: str) -> Zaak | None:
        try:
            response = self.get(url=case_url, headers=CRS_HEADERS)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        case = factory(Zaak, data)

        return case

    @cache_result(
        "{self.base_url}:single_case_information_object:{url}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_single_case_information_object(
        self, url: str
    ) -> ZaakInformatieObject | None:
        try:
            response = self.get(url=url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        case = factory(ZaakInformatieObject, data)

        return case

    def fetch_case_information_objects(
        self, case_url: str
    ) -> list[ZaakInformatieObject]:
        try:
            response = self.get(
                "zaakinformatieobjecten",
                params={"zaak": case_url},
            )
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        case_info_objects = factory(ZaakInformatieObject, data)

        return case_info_objects

    def fetch_status_history_no_cache(self, case_url: str) -> list[Status]:
        try:
            response = self.get("statussen", params={"zaak": case_url})
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        # TODO use pagination_helper?
        statuses = factory(Status, data["results"])

        return statuses

    @cache_result(
        "{self.base_url}:status_history:{case_url}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_status_history(self, case_url: str) -> list[Status]:
        return self.fetch_status_history_no_cache(case_url)

    @cache_result("{self.base_url}:status:{status_url}", timeout=60 * 60)
    def fetch_single_status(self, status_url: str) -> Status | None:
        try:
            response = self.get(url=status_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        status = factory(Status, data)

        return status

    @cache_result(
        "{self.base_url}:case_roles:{case_url}:{role_desc_generic}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_case_roles(
        self, case_url: str, role_desc_generic: str | None = None
    ) -> list[Rol]:
        params = {
            "zaak": case_url,
        }
        if role_desc_generic:
            assert role_desc_generic in RolOmschrijving.values
            params["omschrijvingGeneriek"] = role_desc_generic

        try:
            response = self.get(
                "rollen",
                params=params,
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        roles = factory(Rol, all_data)

        # Taiga #961 process eSuite response to apply ignored filter query
        if role_desc_generic:
            roles = [r for r in roles if r.omschrijving_generiek == role_desc_generic]

        return roles

    # implicitly cached because it uses fetch_case_roles()
    def fetch_roles_for_case_and_bsn(self, case_url: str, bsn: str) -> list[Rol]:
        """
        note we do a query on all case_roles and then manually filter our roles from the result,
        because e-Suite doesn't support querying on both "zaak" AND "betrokkeneIdentificatie__natuurlijkPersoon__inpBsn"

        see Taiga #948
        """
        case_roles = self.fetch_case_roles(case_url)
        if not case_roles:
            return []

        bsn_roles = []
        for role in case_roles:
            if role.betrokkene_type == RolTypes.natuurlijk_persoon:
                inp_bsn = role.betrokkene_identificatie.get("inp_bsn")
                if inp_bsn and inp_bsn == bsn:
                    bsn_roles.append(role)

        return bsn_roles

    # implicitly cached because it uses fetch_case_roles()
    def fetch_roles_for_case_and_kvk_or_rsin(
        self, case_url: str, kvk_or_rsin: str
    ) -> list[Rol]:
        """
        note we do a query on all case_roles and then manually filter our roles from the result,
        because e-Suite doesn't support querying on both "zaak" AND "betrokkeneIdentificatie__nietNatuurlijkPersoon__inn_nnp_id"

        see Taiga #948
        """
        case_roles = self.fetch_case_roles(case_url)
        if not case_roles:
            return []

        roles = []
        for role in case_roles:
            if role.betrokkene_type == RolTypes.niet_natuurlijk_persoon:
                nnp_id = role.betrokkene_identificatie.get("inn_nnp_id")
                if nnp_id and nnp_id == kvk_or_rsin:
                    roles.append(role)

        return roles

    # implicitly cached because it uses fetch_case_roles()
    def fetch_roles_for_case_and_vestigingsnummer(
        self, case_url: str, vestigingsnummer: str
    ) -> list[Rol]:
        """
        note we do a query on all case_roles and then manually filter our roles from the result,
        because e-Suite doesn't support querying on both "zaak" AND "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer"

        see Taiga #948
        """
        case_roles = self.fetch_case_roles(case_url)
        if not case_roles:
            return []

        roles = []
        for role in case_roles:
            if role.betrokkene_type == RolTypes.vestiging:
                identifier = role.betrokkene_identificatie.get("vestigings_nummer")
                if identifier and identifier == vestigingsnummer:
                    roles.append(role)

        return roles

    # not cached because currently only used in info-object download view
    def fetch_case_information_objects_for_case_and_info(
        self, case_url: str, info_object_url: str
    ) -> list[ZaakInformatieObject]:
        try:
            response = self.get(
                "zaakinformatieobjecten",
                params={
                    "zaak": case_url,
                    "informatieobject": info_object_url,
                },
            )
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        case_info_objects = factory(ZaakInformatieObject, data)

        return case_info_objects

    @cache_result(
        "{self.base_url}:single_result:{result_url}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_single_result(self, result_url: str) -> Resultaat | None:
        try:
            response = self.get(url=result_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        result = factory(Resultaat, data)

        return result

    def connect_case_with_document(
        self, case_url: str, document_url: str
    ) -> dict | None:
        try:
            response = self.post(
                "zaakinformatieobjecten",
                json={"zaak": case_url, "informatieobject": document_url},
            )
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        return data


class CatalogiClient(ZgwAPIClient):
    # not cached because only used by tools,
    # and because caching (stale) listings can break lookups
    def fetch_status_types_no_cache(self, case_type_url: str) -> list[StatusType]:
        try:
            response = self.get(
                "statustypen",
                params={"zaaktype": case_type_url},
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        status_types = factory(StatusType, all_data)

        return status_types

    # not cached because only used by tools,
    # and because caching (stale) listings can break lookups
    def fetch_result_types_no_cache(self, case_type_url: str) -> list[ResultaatType]:
        try:
            response = self.get(
                "resultaattypen",
                params={"zaaktype": case_type_url},
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        result_types = factory(ResultaatType, all_data)

        return result_types

    @cache_result(
        "{self.base_url}:status_type:{status_type_url}",
        timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
    )
    def fetch_single_status_type(self, status_type_url: str) -> StatusType | None:
        try:
            response = self.get(url=status_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        status_type = factory(StatusType, data)

        return status_type

    @cache_result(
        "{self.base_url}:resultaat_type:{resultaat_type_url}",
        timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
    )
    def fetch_single_resultaat_type(
        self, resultaat_type_url: str
    ) -> ResultaatType | None:
        try:
            response = self.get(url=resultaat_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        resultaat_type = factory(ResultaatType, data)

        return resultaat_type

    def fetch_zaaktypes_no_cache(self) -> list[ZaakType]:
        try:
            response = self.get("zaaktypen")
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        zaak_types = factory(ZaakType, all_data)

        return zaak_types

    # not cached because only used by cronjob
    # and because caching (stale) listings can break lookups
    def fetch_case_types_by_identification_no_cache(
        self, case_type_identification: str, catalog_url: str | None = None
    ) -> list[ZaakType]:
        try:
            params = {
                "identificatie": case_type_identification,
            }
            if catalog_url:
                params["catalogus"] = catalog_url

            response = self.get("zaaktypen", params=params)
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        zaak_types = factory(ZaakType, all_data)

        return zaak_types

    @cache_result(
        "{self.base_url}:case_type:{case_type_url}",
        timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
    )
    def fetch_single_case_type(self, case_type_url: str) -> ZaakType | None:
        try:
            response = self.get(url=case_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        case_type = factory(ZaakType, data)

        return case_type

    def fetch_catalogs_no_cache(self) -> list[Catalogus]:
        """
        note the eSuite implementation returns status 500 for this call
        """
        try:
            response = self.get("catalogussen")
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        catalogs = factory(Catalogus, all_data)

        return catalogs

    @cache_result(
        "{self.base_url}:information_object_type:{information_object_type_url}",
        timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
    )
    def fetch_single_information_object_type(
        self,
        information_object_type_url: str,
    ) -> InformatieObjectType | None:
        try:
            response = self.get(url=information_object_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        information_object_type = factory(InformatieObjectType, data)

        return information_object_type


class DocumentenClient(ZgwAPIClient):
    def _fetch_single_information_object(
        self, *, url: str | None = None, uuid: str | None = None
    ) -> InformatieObject | None:
        if (url and uuid) or (not url and not uuid):
            raise ValueError("supply either 'url' or 'uuid' argument")

        try:
            if url:
                response = self.get(url=url)
            else:
                response = self.get(f"enkelvoudiginformatieobjecten/{uuid}")
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        info_object = factory(InformatieObject, data)

        return info_object

    def download_document(self, url: str) -> Response | None:
        try:
            response = self.get(url)
            response.raise_for_status()
        except HTTPError as e:
            logger.exception("exception while making request", exc_info=e)
        else:
            return response

    def upload_document(
        self,
        user: SimpleLazyObject,
        file: InMemoryUploadedFile,
        title: str,
        informatieobjecttype_url: str,
        source_organization: str,
    ) -> dict | None:
        document_body = {
            "bronorganisatie": source_organization,
            "creatiedatum": date.today().strftime("%Y-%m-%d"),
            "titel": title,
            "auteur": user.get_full_name(),
            "inhoud": base64.b64encode(file.read()).decode("utf-8"),
            "bestandsomvang": file.size,
            "bestandsnaam": file.name,
            "status": "definitief",
            "indicatieGebruiksrecht": False,
            "taal": "dut",
            "informatieobjecttype": informatieobjecttype_url,
        }

        try:
            response = self.post("enkelvoudiginformatieobjecten", json=document_body)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        return data


class FormClient(ZgwAPIClient):
    def fetch_open_submissions(self, bsn: str) -> list[OpenSubmission]:
        if not bsn:
            return []

        try:
            response = self.get(
                "openstaande-inzendingen",
                params={"bsn": bsn},
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        results = factory(OpenSubmission, all_data)

        return results

    def fetch_open_tasks(self, bsn: str) -> list[OpenTask]:
        if not bsn:
            return []

        response = self.get(
            "openstaande-taken",
            params={"bsn": bsn},
        )
        data = get_json_response(response)
        all_data = list(pagination_helper(self, data))

        results = factory(OpenTask, all_data)

        return results


TClient = TypeVar("TClient", bound=APIClient)


@dataclass(frozen=True)
class ZgwClientResponse:
    """A single response in a MultiZgwClientResult."""

    client: TClient
    result: Any
    exception: Exception | None = None


@dataclass(frozen=True)
class MultiZgwClientProxyResult:
    """Container for a multi-backend responses"""

    responses: list[ZgwClientResponse]

    @property
    def has_errors(self) -> bool:
        return any(r.exception is not None for r in self.responses)

    @property
    def failing_responses(self) -> list[ZgwClientResponse]:
        return list(r for r in self if r.exception is not None)

    @property
    def successful_responses(self) -> list[ZgwClientResponse]:
        return list(r for r in self if r.exception is None)

    @property
    def truthy_responses(self) -> list[ZgwClientResponse]:
        return list(row for row in self.successful_responses if row.result)

    def raise_on_failures(self):
        """Raise a MultiZgwClientProxyError wrapping all errors raised by the clients."""
        if not self.has_errors:
            return

        raise MultiZgwClientProxyError([r.exception for r in self.failing_responses])

    def join_results(self):
        """Join the results for all successful responses in a list."""
        return list(
            result for row in self.successful_responses for result in row.result
        )

    def __iter__(self):
        yield from self.responses


class MultiZgwClientProxy:
    """A proxy to call the same method on multiple ZGW clients in parallel."""

    clients: list[TClient] = []

    def __init__(self, clients: list[TClient]):
        self.clients = clients

        if len(clients) == 0:
            raise ValueError("You must specify at least one client")

    def _call_method(self, method, *args, **kwargs) -> MultiZgwClientProxyResult:
        if not all(hasattr(client, method) for client in self.clients):
            raise AttributeError(f"Method `{method}` does not exist on the clients")

        with parallel() as executor:
            futures_mapping: Mapping[concurrent.futures.Future, TClient] = {}
            for client in self.clients:
                future = executor.submit(
                    getattr(client, method),
                    *args,
                    **kwargs,
                )
                # Remember which future corresponds to which client,
                # so we can associate them in the response
                futures_mapping[future] = client

            responses: list[ZgwClientResponse] = []
            for task in concurrent.futures.as_completed(futures_mapping.keys()):
                result: Any | None = None
                exception: Exception | None = None
                try:
                    result: Any = task.result()
                except BaseException:
                    exception = task.exception()

                responses.append(
                    ZgwClientResponse(
                        result=result, exception=exception, client=futures_mapping[task]
                    )
                )

        # Ensure the response list is deterministic, based on the client order.
        # This is mainly useful for testing but also generally promotes consistent
        # behavior.
        responses.sort(
            key=lambda r: self.clients.index(r.client),
        )
        return MultiZgwClientProxyResult(responses=responses)

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            return self._call_method(name, *args, **kwargs)

        return wrapper


ZgwClientType = Literal["zaak", "catalogi", "document", "form"]
ZgwClientFactoryReturn: TypeAlias = (
    ZakenClient | CatalogiClient | DocumentenClient | FormClient
)


def build_zgw_client_from_service(service: Service) -> ZgwClientFactoryReturn:
    services_to_client_mapping: Mapping[str, Type[ZgwClientFactoryReturn]] = {
        APITypes.zrc: ZakenClient,
        APITypes.ztc: CatalogiClient,
        APITypes.drc: DocumentenClient,
        APITypes.orc: FormClient,
    }

    try:
        client_class = services_to_client_mapping[service.api_type]
    except KeyError:
        raise ValueError(
            f"No client defined for API type {service.api_type} on service {service}"
        )

    client = build_client(service, client_factory=client_class, configured_from=service)
    return client


def _build_all_zgw_clients_for_type(
    type_: ZgwClientType,
) -> list[ZakenClient | CatalogiClient | DocumentenClient | FormClient]:
    config = OpenZaakConfig.get_solo()
    services_to_client_mapping: Mapping[ZgwClientType, str] = {
        "zaak": "zrc_service",
        "catalogi": "ztc_service",
        "document": "drc_service",
        "form": "form_service",
    }

    return [
        build_zgw_client_from_service(
            getattr(api_group, services_to_client_mapping[type_])
        )
        for api_group in config.api_groups.all()
    ]


_SINGLETON_ZGW_CLIENT_DEPRECATION_MESSAGE = (
    "Singleton ZGW client factories are in the process of being deprecated in favour of"
    " multi-ZGW backend aware implementations. Use build_*_clients() or build_zgw_"
    "client_from_service() instead."
)
warnings.filterwarnings(
    "once", _SINGLETON_ZGW_CLIENT_DEPRECATION_MESSAGE, category=DeprecationWarning
)


def build_zaken_client() -> ZakenClient:
    warnings.warn(_SINGLETON_ZGW_CLIENT_DEPRECATION_MESSAGE, DeprecationWarning)
    config = OpenZaakConfig.get_solo()
    return build_zgw_client_from_service(config.zaak_service)


def build_zaken_clients() -> list[ZakenClient]:
    return _build_all_zgw_clients_for_type("zaak")


def build_catalogi_client() -> CatalogiClient:
    warnings.warn(_SINGLETON_ZGW_CLIENT_DEPRECATION_MESSAGE, DeprecationWarning)
    config = OpenZaakConfig.get_solo()
    return build_zgw_client_from_service(config.catalogi_service)


def build_catalogi_clients() -> list[CatalogiClient]:
    return _build_all_zgw_clients_for_type("catalogi")


def build_documenten_client() -> DocumentenClient:
    warnings.warn(_SINGLETON_ZGW_CLIENT_DEPRECATION_MESSAGE, DeprecationWarning)
    config = OpenZaakConfig.get_solo()
    return build_zgw_client_from_service(config.document_service)


def build_documenten_clients() -> list[DocumentenClient]:
    return _build_all_zgw_clients_for_type("document")


def build_forms_client() -> FormClient | None:
    warnings.warn(_SINGLETON_ZGW_CLIENT_DEPRECATION_MESSAGE, DeprecationWarning)
    config = OpenZaakConfig.get_solo()

    # Special case: though we require all other services,
    # the form_service may not in fact be set
    if not config.form_service:
        return None

    return build_zgw_client_from_service(config.form_service)


def build_forms_clients() -> list[FormClient]:
    return _build_all_zgw_clients_for_type("form")
