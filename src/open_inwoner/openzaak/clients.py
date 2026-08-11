import base64
import concurrent.futures
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, Mapping, Type, TypeAlias, TypeVar, cast

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.functional import SimpleLazyObject

import structlog
from requests import Response
from zgw_consumers.api_models.catalogi import Catalogus
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes
from zgw_consumers.client import build_client
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.service import pagination_helper

from open_inwoner.accounts.user_identification import (
    BSNIdentification,
    KVKIdentification,
    UserIdentification,
)
from open_inwoner.openzaak.api_models import InformatieObject
from open_inwoner.openzaak.exceptions import (
    MultiZgwClientProxyError,
    ZgwAPIClientError,
    ZgwAPIDataError,
    ZgwAPIInvalidJSONError,
    ZgwAPINetworkError,
    ZgwAPIServerError,
)
from open_inwoner.utils.api import BaseAPIClient
from open_inwoner.utils.concurrency import TimedParallel
from open_inwoner.utils.decorators import cache as cache_result

from .api_models import (
    Formulier,
    InformatieObjectType,
    OpenstaandeTaak,
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
from .utils import omschrijving_generiek_matches

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}

logger = structlog.stdlib.get_logger(__name__)


class ZgwAPIClient(BaseAPIClient):
    """A client for interacting with ZGW services."""

    network_error_type = ZgwAPINetworkError
    client_error_type = ZgwAPIClientError
    server_error_type = ZgwAPIServerError
    invalid_json_error_type = ZgwAPIInvalidJSONError
    data_error_type = ZgwAPIDataError

    configured_from: Service

    def __init__(self, *args, **kwargs):
        self.configured_from = kwargs.pop("configured_from")
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"Client {self.__class__.__name__} for {self.base_url}"


class ZakenClient(ZgwAPIClient):
    use_openzaak_120_params: bool
    fetch_rollen_with_betrokkene_type: bool
    zaak_max_confidentiality: str
    limit_user_visible_cases_to_role: str | None
    cache_zaken_timeout: int
    max_requests: int

    def __init__(
        self,
        *args,
        use_openzaak_120_params: bool,
        fetch_rollen_with_betrokkene_type: bool,
        zaak_max_confidentiality: str,
        limit_user_visible_cases_to_role: str | None = None,
        cache_zaken_timeout: int | None = None,
        max_requests: int | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.use_openzaak_120_params = use_openzaak_120_params
        self.fetch_rollen_with_betrokkene_type = fetch_rollen_with_betrokkene_type
        self.zaak_max_confidentiality = zaak_max_confidentiality
        self.limit_user_visible_cases_to_role = limit_user_visible_cases_to_role
        self.cache_zaken_timeout = cache_zaken_timeout or 0
        # `pagination_helper` treats 0 the same as None: no cap at all. Falling back
        # on the setting keeps an unconfigured or zeroed client from following every
        # page of a user's zaken.
        self.max_requests = max_requests or settings.ZGW_MAX_REQUESTS

    def fetch_zaken(
        self,
        user_identification: UserIdentification,
        use_rsin: bool = True,
        identificatie: str | None = None,
    ) -> list[Zaak]:
        match user_identification:
            case BSNIdentification():
                return self.fetch_zaken_by_bsn(
                    user_identification.bsn,
                    identificatie=identificatie,
                )
            case KVKIdentification():
                if use_rsin:
                    if not user_identification.rsin:
                        logger.warning(
                            "Skipping zaken fetch: group requires RSIN but user has none",
                            kvk=user_identification.kvk,
                        )
                        return []
                    kvk_or_rsin = user_identification.rsin
                else:
                    kvk_or_rsin = user_identification.kvk
                return self.fetch_zaken_for_company(
                    kvk_or_rsin=kvk_or_rsin,
                    vestigingsnummer=user_identification.vestigingsnummer,
                    zaak_identificatie=identificatie,
                )
            case _:
                raise TypeError(
                    f"Unexpected identity type: {type(user_identification)}"
                )

    @cache_result(
        "{self.base_url}:zaken:{user_bsn}:{self.max_requests}:{identificatie}:{self.zaak_max_confidentiality}:{self.limit_user_visible_cases_to_role}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_zaken_by_bsn(
        self,
        user_bsn: str,
        identificatie: str | None = None,
    ) -> list[Zaak]:
        """
        retrieve zaken for particular user with allowed confidentiality level

        The pagination bound is `self.max_requests` rather than an argument, so that
        every caller of a given client necessarily agrees on it. The cache key varies
        on it, and callers that disagreed would land in separate entries: the login
        warm-up would populate one no page view reads.

        :param:identificatie - used to filter the zaken by a specific identification
        """
        params = {
            "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": user_bsn,
            "maximaleVertrouwelijkheidaanduiding": self.zaak_max_confidentiality,
        }
        if identificatie:
            params.update({"identificatie": identificatie})
        if self.limit_user_visible_cases_to_role:
            params.update(
                {"rol__omschrijvingGeneriek": self.limit_user_visible_cases_to_role}
            )

        response = self.get(
            "zaken",
            params=params,
            headers=CRS_HEADERS,
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(
            pagination_helper(
                self,
                data,
                max_requests=self.max_requests,
                headers=CRS_HEADERS,
            )
        )
        return self.factory(Zaak, all_data)

    @cache_result(
        "{self.base_url}:zaken:{kvk_or_rsin}:{vestigingsnummer}:{self.max_requests}:{zaak_identificatie}:{self.zaak_max_confidentiality}:{self.limit_user_visible_cases_to_role}:{self.use_openzaak_120_params}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_zaken_for_company(
        self,
        kvk_or_rsin: str | None = None,
        zaak_identificatie: str | None = None,
        vestigingsnummer: str | None = None,
    ) -> list[Zaak]:
        """
        retrieve zaken for particular company with allowed confidentiality level

        See `fetch_zaken_by_bsn` for why the pagination bound is client state rather
        than an argument. `use_openzaak_120_params` is in the cache key for a related
        reason: it decides which query parameter names are sent, so entries collected
        under one style must not be served after an admin switches to the other.

        :param kvk_or_rsin: - used to filter the zaken by a KVK number or RSIN (configured via OpenZaakConfig)
        :param zaak_identificatie: - used to filter the zaken by a unique Zaak identification number
        :param vestigingsnummer: - used to filter the zaken by a vestigingsnummer
        """

        if not (kvk_or_rsin or vestigingsnummer):
            raise ValueError(
                "You must set either a `kvk_or_rsin` or `vestigingsnummer`"
            )

        params = {
            "maximaleVertrouwelijkheidaanduiding": self.zaak_max_confidentiality,
        }

        vestigingsnummer_param = (
            "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer"
        )
        kvk_rsin_param = "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId"

        if self.use_openzaak_120_params:
            vestigingsnummer_param = (
                "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__vestigingsNummer"
            )
            kvk_rsin_param = (
                "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__kvkNummer"
            )

        if vestigingsnummer:
            params.update({vestigingsnummer_param: vestigingsnummer})

        if kvk_or_rsin:
            params.update({kvk_rsin_param: kvk_or_rsin})

        if zaak_identificatie:
            params.update({"identificatie": zaak_identificatie})

        if self.limit_user_visible_cases_to_role:
            params.update(
                {"rol__omschrijvingGeneriek": self.limit_user_visible_cases_to_role}
            )

        response = self.get(
            "zaken",
            params=params,
            headers=CRS_HEADERS,
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(
            pagination_helper(
                self,
                data,
                max_requests=self.max_requests,
                headers=CRS_HEADERS,
            )
        )
        return self.factory(Zaak, all_data)

    @cache_result(
        "{self.base_url}:single_zaak:{zaak_uuid}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_single_zaak(self, zaak_uuid: str) -> Zaak:
        response = self.get(f"zaken/{zaak_uuid}", headers=CRS_HEADERS)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(Zaak, data)

    def fetch_zaak_by_url_no_cache(self, zaak_url: str) -> Zaak:
        response = self.get(url=zaak_url, headers=CRS_HEADERS)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(Zaak, data)

    @cache_result(
        "{self.base_url}:single_zaak_information_object:{url}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_single_zaak_information_object(self, url: str) -> ZaakInformatieObject:
        response = self.get(url=url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(ZaakInformatieObject, data)

    def fetch_zaak_information_objects(
        self, zaak_url: str
    ) -> list[ZaakInformatieObject]:
        response = self.get(
            "zaakinformatieobjecten",
            params={"zaak": zaak_url},
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(ZaakInformatieObject, data)

    def fetch_status_history_no_cache(self, zaak_url: str) -> list[Status]:
        response = self.get("statussen", params={"zaak": zaak_url})
        self.raise_for_status(response)
        data = self.parse_json(response)
        # TODO use pagination_helper?
        return self.factory(Status, data["results"])

    @cache_result(
        "{self.base_url}:status_history:{zaak_url}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_status_history(self, zaak_url: str) -> list[Status]:
        return self.fetch_status_history_no_cache(zaak_url)

    @cache_result(
        "{self.base_url}:status:{status_url}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_single_status(self, status_url: str) -> Status:
        response = self.get(url=status_url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(Status, data)

    @cache_result(
        "{self.base_url}:zaak_roles:{zaak_url}:{role_desc_generic}:{betrokkene_type}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_zaak_roles(
        self,
        zaak_url: str,
        role_desc_generic: str | None = None,
        betrokkene_type: str | None = None,
    ) -> list[Rol]:
        params = {
            "zaak": zaak_url,
        }
        if role_desc_generic:
            if role_desc_generic not in RolOmschrijving.values:
                raise ValueError(f"{role_desc_generic} is not a known RolOmschrijving")

            params["omschrijvingGeneriek"] = role_desc_generic

        # Add betrokkene_type to params if provided
        if betrokkene_type:
            params["betrokkeneType"] = betrokkene_type

        response = self.get(
            "rollen",
            params=params,
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        roles = self.factory(Rol, all_data)

        # Taiga #961 process eSuite response to apply ignored filter query
        if role_desc_generic:
            roles = [
                r
                for r in roles
                if omschrijving_generiek_matches(
                    r.omschrijving_generiek, role_desc_generic
                )
            ]

        return roles

    # implicitly cached because it uses fetch_zaak_roles()
    def fetch_roles_for_zaak_and_bsn(self, zaak_url: str, bsn: str) -> list[Rol]:
        """
        note we do a query on all zaak_roles and then manually filter our roles from the result,
        because e-Suite doesn't support querying on both "zaak" AND "betrokkeneIdentificatie__natuurlijkPersoon__inpBsn"

        see Taiga #948
        """
        betrokkene_type = (
            RolTypes.natuurlijk_persoon
            if self.fetch_rollen_with_betrokkene_type
            else None
        )
        zaak_roles = self.fetch_zaak_roles(zaak_url, betrokkene_type=betrokkene_type)
        if not zaak_roles:
            return []

        bsn_roles = []
        for role in zaak_roles:
            if role.betrokkene_type == RolTypes.natuurlijk_persoon:
                inp_bsn = role.betrokkene_identificatie.get("inp_bsn")
                if inp_bsn and inp_bsn == bsn:
                    bsn_roles.append(role)

        return bsn_roles

    # implicitly cached because it uses fetch_zaak_roles()
    def fetch_roles_for_zaak_and_kvk_or_rsin(
        self, zaak_url: str, kvk_or_rsin: str
    ) -> list[Rol]:
        """
        note we do a query on all zaak_roles and then manually filter our roles from the result,
        because e-Suite doesn't support querying on both "zaak" AND "betrokkeneIdentificatie__nietNatuurlijkPersoon__inn_nnp_id"

        see Taiga #948
        """
        betrokkene_type = (
            RolTypes.niet_natuurlijk_persoon
            if self.fetch_rollen_with_betrokkene_type
            else None
        )
        zaak_roles = self.fetch_zaak_roles(zaak_url, betrokkene_type=betrokkene_type)
        if not zaak_roles:
            return []

        roles = []
        for role in zaak_roles:
            if role.betrokkene_type == RolTypes.niet_natuurlijk_persoon:
                nnp_id = role.betrokkene_identificatie.get("inn_nnp_id")
                if nnp_id and nnp_id == kvk_or_rsin:
                    roles.append(role)

        return roles

    # implicitly cached because it uses fetch_zaak_roles()
    def fetch_roles_for_zaak_and_vestigingsnummer(
        self, zaak_url: str, vestigingsnummer: str
    ) -> list[Rol]:
        """
        note we do a query on all zaak_roles and then manually filter our roles from the result,
        because e-Suite doesn't support querying on both "zaak" AND "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer"

        see Taiga #948
        """
        betrokkene_type = (
            RolTypes.vestiging if self.fetch_rollen_with_betrokkene_type else None
        )
        zaak_roles = self.fetch_zaak_roles(zaak_url, betrokkene_type=betrokkene_type)
        if not zaak_roles:
            return []

        roles = []
        for role in zaak_roles:
            if role.betrokkene_type == RolTypes.vestiging:
                identifier = role.betrokkene_identificatie.get("vestigings_nummer")
                if identifier and identifier == vestigingsnummer:
                    roles.append(role)

        return roles

    def fetch_rollen_for_user(
        self,
        zaak_url: str,
        user_identification: UserIdentification,
        use_rsin: bool = True,
    ) -> list[Rol]:
        match user_identification:
            case BSNIdentification():
                return self.fetch_roles_for_zaak_and_bsn(
                    zaak_url, user_identification.bsn
                )
            case KVKIdentification():
                if user_identification.vestigingsnummer:
                    return self.fetch_roles_for_zaak_and_vestigingsnummer(
                        zaak_url, user_identification.vestigingsnummer
                    )
                kvk_or_rsin = (
                    user_identification.rsin
                    if use_rsin and user_identification.rsin
                    else user_identification.kvk
                )
                return self.fetch_roles_for_zaak_and_kvk_or_rsin(zaak_url, kvk_or_rsin)
            case _:
                raise TypeError(
                    f"Unexpected user_identification type: {type(user_identification)}"
                )

    # not cached because currently only used in info-object download view
    def fetch_zaak_information_objects_for_zaak_and_info(
        self, zaak_url: str, info_object_url: str
    ) -> list[ZaakInformatieObject]:
        response = self.get(
            "zaakinformatieobjecten",
            params={
                "zaak": zaak_url,
                "informatieobject": info_object_url,
            },
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(ZaakInformatieObject, data)

    @cache_result(
        "{self.base_url}:single_result:{result_url}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def fetch_single_result(self, result_url: str) -> Resultaat:
        response = self.get(url=result_url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(Resultaat, data)

    def connect_case_with_document(self, zaak_url: str, document_url: str) -> dict:
        response = self.post(
            "zaakinformatieobjecten",
            json={"zaak": zaak_url, "informatieobject": document_url},
        )
        self.raise_for_status(response)
        return self.parse_json(response)


class CatalogiClient(ZgwAPIClient):
    cache_catalogi_timeout: int

    def __init__(self, *args, cache_catalogi_timeout: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_catalogi_timeout = cache_catalogi_timeout or 0

    # not cached because only used by tools,
    # and because caching (stale) listings can break lookups
    def fetch_statustypes_no_cache(self, zaaktype_url: str) -> list[StatusType]:
        response = self.get(
            "statustypen",
            params={"zaaktype": zaaktype_url},
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        return self.factory(StatusType, all_data)

    # not cached because only used by tools,
    # and because caching (stale) listings can break lookups
    def fetch_resultaattypes_no_cache(self, zaaktype_url: str) -> list[ResultaatType]:
        response = self.get(
            "resultaattypen",
            params={"zaaktype": zaaktype_url},
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        return self.factory(ResultaatType, all_data)

    @cache_result(
        "{self.base_url}:status_type:{status_type_url}",
        timeout=lambda self: self.cache_catalogi_timeout,
    )
    def fetch_single_status_type(self, status_type_url: str) -> StatusType:
        response = self.get(url=status_type_url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(StatusType, data)

    @cache_result(
        "{self.base_url}:resultaat_type:{resultaat_type_url}",
        timeout=lambda self: self.cache_catalogi_timeout,
    )
    def fetch_single_resultaat_type(self, resultaat_type_url: str) -> ResultaatType:
        response = self.get(url=resultaat_type_url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(ResultaatType, data)

    def fetch_zaaktypes_no_cache(
        self, identificatie: str | None = None
    ) -> list[ZaakType]:
        params = None
        if identificatie:
            params = {"identificatie": identificatie}

        response = self.get("zaaktypen", params=params)
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        return self.factory(ZaakType, all_data)

    @cache_result(
        "{self.base_url}:zaaktype:{zaaktype_url}",
        timeout=lambda self: self.cache_catalogi_timeout,
    )
    def fetch_single_zaaktype(self, zaaktype_url: str) -> ZaakType:
        response = self.get(url=zaaktype_url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(ZaakType, data)

    def fetch_catalogs_no_cache(self) -> list[Catalogus]:
        """
        note the eSuite implementation returns status 500 for this call
        """
        response = self.get("catalogussen")
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        return self.factory(Catalogus, all_data)

    @cache_result(
        "{self.base_url}:information_object_type:{information_object_type_url}",
        timeout=lambda self: self.cache_catalogi_timeout,
    )
    def fetch_single_information_object_type(
        self,
        information_object_type_url: str,
    ) -> InformatieObjectType:
        response = self.get(url=information_object_type_url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(InformatieObjectType, data)


class DocumentenClient(ZgwAPIClient):
    cache_zaken_timeout: int

    def __init__(self, *args, cache_zaken_timeout: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_zaken_timeout = cache_zaken_timeout or 0

    @cache_result(
        "{self.base_url}:information_object:{url}:{uuid}",
        timeout=lambda self: self.cache_zaken_timeout,
    )
    def _fetch_single_information_object(
        self, *, url: str | None = None, uuid: str | None = None
    ) -> InformatieObject:
        if (url and uuid) or (not url and not uuid):
            raise ValueError("supply either 'url' or 'uuid' argument")

        if url:
            response = self.get(url=url)
        else:
            response = self.get(f"enkelvoudiginformatieobjecten/{uuid}")
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(InformatieObject, data)

    def download_document(self, url: str) -> Response:
        response = self.get(url)
        self.raise_for_status(response)
        return response

    def upload_document(
        self,
        user: SimpleLazyObject,
        file: InMemoryUploadedFile,
        title: str,
        informatieobjecttype_url: str,
        source_organization: str,
    ) -> dict:
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
        if file.content_type:
            document_body["formaat"] = file.content_type

        response = self.post("enkelvoudiginformatieobjecten", json=document_body)
        self.raise_for_status(response)
        return self.parse_json(response)


class FormulierenClient(ZgwAPIClient):
    max_requests: int

    def __init__(self, *args, max_requests: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        # `pagination_helper` treats 0 the same as None: no cap at all. Falling back
        # on the setting keeps an unconfigured or zeroed client from following every
        # page of a user's inzendingen.
        self.max_requests = max_requests or settings.ZGW_MAX_REQUESTS

    def fetch_formulieren(
        self,
        user_identification: UserIdentification,
        use_rsin: bool = True,
    ) -> list[Formulier]:
        match user_identification:
            case BSNIdentification():
                return self.fetch_formulieren_by_bsn(user_identification.bsn)
            case KVKIdentification():
                if use_rsin:
                    # forms service does not support RSIN; skip when group is configured for RSIN
                    if not user_identification.rsin:
                        logger.warning(
                            "Skipping formulieren fetch: group requires RSIN but user has none",
                            kvk=user_identification.kvk,
                        )
                    return []
                return self.fetch_formulieren_by_kvk(
                    user_identification.kvk,
                    vestigingsnummer=user_identification.vestigingsnummer,
                )
            case _:
                raise TypeError(
                    f"Unexpected identity type: {type(user_identification)}"
                )

    def fetch_formulieren_by_bsn(self, user_bsn: str) -> list[Formulier]:
        response = self.get(
            "openstaande-inzendingen",
            params={"bsn": user_bsn},
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data, max_requests=self.max_requests))
        return self.factory(Formulier, all_data)

    def fetch_formulieren_by_kvk(
        self,
        user_kvk: str,
        vestigingsnummer: str | None,
    ) -> list[Formulier]:
        request_params = {"kvk": user_kvk}
        if vestigingsnummer:
            request_params["vestigingsnummer"] = vestigingsnummer

        response = self.get(
            "openstaande-inzendingen",
            params=request_params,
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data, max_requests=self.max_requests))
        return self.factory(Formulier, all_data)

    def fetch_open_tasks(self, bsn: str) -> list[OpenstaandeTaak]:
        if not bsn:
            return []

        response = self.get(
            "openstaande-taken",
            params={"bsn": bsn},
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        return self.factory(OpenstaandeTaak, all_data)


TClient = TypeVar("TClient", bound=BaseAPIClient)


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

        with TimedParallel(name=f"multi_zgw_client_proxy.{method}") as executor:
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
            # No timeout: this proxy is used for admin/diagnostic calls
            # where waiting for every client to finish is the intended
            # behaviour.
            for task in executor.as_completed(futures_mapping.keys()):
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
    ZakenClient | CatalogiClient | DocumentenClient | FormulierenClient
)


def build_zgw_client_from_service(
    service: Service, **client_init_kwargs
) -> ZgwClientFactoryReturn:
    services_to_client_mapping: Mapping[str, Type[ZgwClientFactoryReturn]] = {
        APITypes.zrc: ZakenClient,
        APITypes.ztc: CatalogiClient,
        APITypes.drc: DocumentenClient,
        APITypes.orc: FormulierenClient,
    }

    try:
        client_class = services_to_client_mapping[service.api_type]
    except KeyError:
        raise ValueError(
            f"No client defined for API type {service.api_type} on service {service}"
        ) from None

    client = build_client(
        service,
        client_factory=client_class,
        configured_from=service,
        **client_init_kwargs,
    )
    return client


def _build_all_zgw_clients_for_type(
    type_: ZgwClientType,
) -> list[ZakenClient | CatalogiClient | DocumentenClient | FormulierenClient]:
    config = OpenZaakConfig.get_solo()
    services_to_client_mapping: Mapping[ZgwClientType, str] = {
        "zaak": "zrc_service",
        "catalogi": "ztc_service",
        "document": "drc_service",
        "form": "form_service",
    }

    clients = []
    for api_group in config.api_groups.all():
        service = getattr(api_group, services_to_client_mapping[type_])
        if service is not None:
            # Special case for ZakenClient to pass use_openzaak_120_params
            client_init_kwargs = {}
            if type_ == "zaak":
                client_init_kwargs = {
                    "use_openzaak_120_params": api_group.fetch_eherkenning_zaken_with_openzaak_120_params,
                    "fetch_rollen_with_betrokkene_type": api_group.fetch_rollen_with_betrokkene_type,
                    "zaak_max_confidentiality": config.zaak_max_confidentiality,
                    "limit_user_visible_cases_to_role": config.limit_user_visible_cases_to_role,
                    "cache_zaken_timeout": api_group.cache_zaken_timeout,
                }
            elif type_ == "catalogi":
                client_init_kwargs = {
                    "cache_catalogi_timeout": api_group.cache_catalogi_timeout,
                }
            elif type_ == "document":
                client_init_kwargs = {
                    "cache_zaken_timeout": api_group.cache_zaken_timeout,
                }

            client = build_zgw_client_from_service(service, **client_init_kwargs)
            clients.append(client)

    return clients


def build_zaken_clients() -> list[ZakenClient]:
    return cast(list[ZakenClient], _build_all_zgw_clients_for_type("zaak"))


def build_catalogi_clients() -> list[CatalogiClient]:
    return cast(list[CatalogiClient], _build_all_zgw_clients_for_type("catalogi"))


def build_documenten_clients() -> list[DocumentenClient]:
    return cast(list[DocumentenClient], _build_all_zgw_clients_for_type("document"))


def build_forms_clients() -> list[FormulierenClient]:
    return cast(list[FormulierenClient], _build_all_zgw_clients_for_type("form"))
