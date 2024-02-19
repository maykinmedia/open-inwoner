import base64
import logging
from datetime import date
from typing import List, Optional

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.functional import SimpleLazyObject

from ape_pie.client import APIClient
from requests import HTTPError, RequestException, Response
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes
from zgw_consumers.client import build_client as _build_client
from zgw_consumers.service import pagination_helper

from open_inwoner.openzaak.api_models import InformatieObject
from open_inwoner.utils.api import ClientError, get_json_response

from ..utils.decorators import cache as cache_result
from .api_models import (
    InformatieObjectType,
    OpenSubmission,
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


class ZakenClient(APIClient):
    @cache_result(
        "cases:{user_bsn}:{max_requests}:{identificatie}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_cases(
        self,
        user_bsn: str,
        max_requests: Optional[int] = 4,
        identificatie: Optional[str] = None,
    ) -> List[Zaak]:
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
        "cases:{kvk_or_rsin}:{vestigingsnummer}:{max_requests}:{zaak_identificatie}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_cases_by_kvk_or_rsin(
        self,
        kvk_or_rsin: Optional[str],
        max_requests: Optional[int] = 4,
        zaak_identificatie: Optional[str] = None,
        vestigingsnummer: Optional[str] = None,
    ) -> List[Zaak]:
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

    @cache_result("single_case:{case_uuid}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
    def fetch_single_case(self, case_uuid: str) -> Optional[Zaak]:
        try:
            response = self.get(f"zaken/{case_uuid}", headers=CRS_HEADERS)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        case = factory(Zaak, data)

        return case

    def fetch_case_by_url_no_cache(self, case_url: str) -> Optional[Zaak]:
        try:
            response = self.get(url=case_url, headers=CRS_HEADERS)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        case = factory(Zaak, data)

        return case

    @cache_result(
        "single_case_information_object:{url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT
    )
    def fetch_single_case_information_object(
        self, url: str
    ) -> Optional[ZaakInformatieObject]:
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
    ) -> List[ZaakInformatieObject]:
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

    def fetch_status_history_no_cache(self, case_url: str) -> List[Status]:
        try:
            response = self.get("statussen", params={"zaak": case_url})
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        # TODO use pagination_helper?
        statuses = factory(Status, data["results"])

        return statuses

    @cache_result("status_history:{case_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
    def fetch_status_history(self, case_url: str) -> List[Status]:
        return self.fetch_status_history_no_cache(case_url)

    @cache_result("status:{status_url}", timeout=60 * 60)
    def fetch_single_status(self, status_url: str) -> Optional[Status]:
        try:
            response = self.get(url=status_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        status = factory(Status, data)

        return status

    @cache_result(
        "case_roles:{case_url}:{role_desc_generic}",
        timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT,
    )
    def fetch_case_roles(
        self, case_url: str, role_desc_generic: Optional[str] = None
    ) -> List[Rol]:
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
    def fetch_roles_for_case_and_bsn(self, case_url: str, bsn: str) -> List[Rol]:
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
    ) -> List[Rol]:
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
    ) -> List[Rol]:
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
    ) -> List[ZaakInformatieObject]:
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
        "single_result:{result_url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT
    )
    def fetch_single_result(self, result_url: str) -> Optional[Resultaat]:
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
    ) -> Optional[dict]:
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


class CatalogiClient(APIClient):
    # not cached because only used by tools,
    # and because caching (stale) listings can break lookups
    def fetch_status_types_no_cache(self, case_type_url: str) -> List[StatusType]:
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
    def fetch_result_types_no_cache(self, case_type_url: str) -> List[ResultaatType]:
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
        "status_type:{status_type_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT
    )
    def fetch_single_status_type(self, status_type_url: str) -> Optional[StatusType]:
        try:
            response = self.get(url=status_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        status_type = factory(StatusType, data)

        return status_type

    @cache_result(
        "resultaat_type:{resultaat_type_url}",
        timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
    )
    def fetch_single_resultaat_type(
        self, resultaat_type_url: str
    ) -> Optional[ResultaatType]:
        try:
            response = self.get(url=resultaat_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        resultaat_type = factory(ResultaatType, data)

        return resultaat_type

    def fetch_zaaktypes_no_cache(self) -> List[ZaakType]:
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
        self, case_type_identification: str, catalog_url: Optional[str] = None
    ) -> List[ZaakType]:
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
        "case_type:{case_type_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT
    )
    def fetch_single_case_type(self, case_type_url: str) -> Optional[ZaakType]:
        try:
            response = self.get(url=case_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        case_type = factory(ZaakType, data)

        return case_type

    def fetch_catalogs_no_cache(self) -> List[Catalogus]:
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
        "information_object_type:{information_object_type_url}",
        timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
    )
    def fetch_single_information_object_type(
        self,
        information_object_type_url: str,
    ) -> Optional[InformatieObjectType]:
        try:
            response = self.get(url=information_object_type_url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        information_object_type = factory(InformatieObjectType, data)

        return information_object_type


class DocumentenClient(APIClient):
    def _fetch_single_information_object(
        self, *, url: Optional[str] = None, uuid: Optional[str] = None
    ) -> Optional[InformatieObject]:
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

    def download_document(self, url: str) -> Optional[Response]:
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
    ) -> Optional[dict]:
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


class FormClient(APIClient):
    def fetch_open_submissions(self, bsn: str) -> List[OpenSubmission]:
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


def build_client(type_) -> Optional[APIClient]:
    config = OpenZaakConfig.get_solo()
    services_to_client_mapping = {
        "zaak": ZakenClient,
        "catalogi": CatalogiClient,
        "document": DocumentenClient,
        "form": FormClient,
    }
    if client_class := services_to_client_mapping.get(type_):
        service = getattr(config, f"{type_}_service")
        if service:
            client = _build_client(service, client_factory=client_class)
            return client

    logger.warning("no service defined for %s", type_)
    return None
