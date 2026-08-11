import structlog
from zgw_consumers.client import build_client
from zgw_consumers.utils import pagination_helper

from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.utils.api import BaseAPIClient
from open_inwoner.utils.decorators import cache as cache_result

from .api_models import (
    ContactMoment,
    ContactMomentCreateData,
    Klant,
    KlantContactMoment,
    KlantContactRol,
    ObjectContactMoment,
)
from .constants import DEFAULT_KLANTCONTACTMOMENTEN_MAX_REQUESTS
from .exceptions import (
    KlantAPIClientError,
    KlantAPIDataError,
    KlantAPIInvalidJSONError,
    KlantAPINetworkError,
    KlantAPIServerError,
)
from .models import ESuiteKlantConfig

logger = structlog.stdlib.get_logger(__name__)


class KlantAPIClient(BaseAPIClient):
    """Base API client for all eSuite klant API services."""

    network_error_type = KlantAPINetworkError
    client_error_type = KlantAPIClientError
    server_error_type = KlantAPIServerError
    invalid_json_error_type = KlantAPIInvalidJSONError
    data_error_type = KlantAPIDataError


class KlantenClient(KlantAPIClient):
    def retrieve_klant(
        self,
        user_bsn: str | None = None,
        user_kvk_or_rsin: str | None = None,
        vestigingsnummer: str | None = None,
    ) -> Klant:
        if not user_bsn and not user_kvk_or_rsin:
            return

        # this is technically a search operation and could return multiple records
        if user_bsn:
            klanten = self.retrieve_klanten_for_bsn(user_bsn)
        elif user_kvk_or_rsin:
            klanten = self.retrieve_klanten_for_kvk_or_rsin(
                user_kvk_or_rsin=user_kvk_or_rsin, vestigingsnummer=vestigingsnummer
            )

        if klanten:
            # let's use the first one
            return klanten[0]
        else:
            return

    def retrieve_klanten_for_bsn(self, user_bsn: str) -> list[Klant]:
        response = self.get(
            "klanten",
            params={"subjectNatuurlijkPersoon__inpBsn": user_bsn},
        )
        self.raise_for_status(response)
        raw_json_data = self.parse_json(response)
        paginated_data = list(pagination_helper(self, raw_json_data))
        return self.factory(Klant, paginated_data)

    def retrieve_klanten_for_kvk_or_rsin(
        self, user_kvk_or_rsin: str, *, vestigingsnummer: str | None = None
    ) -> list[Klant]:
        params = {}
        if vestigingsnummer:
            params["subjectVestiging__vestigingsNummer"] = vestigingsnummer
        if user_kvk_or_rsin:
            params["subjectNietNatuurlijkPersoon__innNnpId"] = user_kvk_or_rsin
        response = self.get("klanten", params=params)
        self.raise_for_status(response)
        raw_json_data = self.parse_json(response)
        all_data = list(pagination_helper(self, raw_json_data))
        return self.factory(Klant, all_data)

    def partial_update_klant(self, klant: Klant, update_data) -> Klant:
        response = self.patch(url=klant.url, json=update_data)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(Klant, data)


class ContactmomentenClient(KlantAPIClient):
    cache_timeout: int

    def __init__(self, *args, cache_timeout: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_timeout = cache_timeout or 0

    #
    # contactmomenten
    #
    def create_contactmoment(
        self,
        data: ContactMomentCreateData,
        *,
        klant: Klant | None = None,
        rol: str | None = KlantContactRol.BELANGHEBBENDE,
    ) -> ContactMoment:
        response = self.post("contactmomenten", json=data)
        self.raise_for_status(response)
        raw_data = self.parse_json(response)
        contactmoment = self.factory(ContactMoment, raw_data)

        if klant:
            # relate contact to klant though a klantcontactmoment
            response = self.post(
                "klantcontactmomenten",
                json={
                    "klant": klant.url,
                    "contactmoment": contactmoment.url,
                    "rol": rol,
                },
            )
            self.raise_for_status(response)

        return contactmoment

    @cache_result(
        "{self.base_url}:contactmoment:{url}",
        timeout=lambda self: self.cache_timeout,
    )
    def retrieve_contactmoment(self, url) -> ContactMoment:
        response = self.get(url)
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(ContactMoment, data)

    #
    # objectcontactmomenten
    #
    def create_objectcontactmoment(
        self,
        contactmoment: ContactMoment,
        zaak: Zaak,
        object_type: str = "zaak",
    ) -> ObjectContactMoment:
        response = self.post(
            "objectcontactmomenten",
            json={
                "contactmoment": contactmoment.url,
                "object": zaak.url,
                "objectType": object_type,
            },
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        return self.factory(ObjectContactMoment, data)

    def retrieve_objectcontactmomenten_for_zaak(
        self, zaak: Zaak
    ) -> list[ObjectContactMoment]:
        response = self.get("objectcontactmomenten", params={"object": zaak.url})
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        object_contact_momenten = self.factory(ObjectContactMoment, all_data)

        # resolve linked resources
        contactmoment_mapping = {}
        for ocm in object_contact_momenten:
            if not ocm.object == zaak.url:
                raise ValueError("objectcontactmoment not linked to zaak")

            ocm.object = zaak

            contactmoment_url = ocm.contactmoment
            if contactmoment_url in contactmoment_mapping:
                ocm.contactmoment = contactmoment_mapping[contactmoment_url]
            else:
                ocm.contactmoment = self.retrieve_contactmoment(contactmoment_url)
                contactmoment_mapping[contactmoment_url] = ocm.contactmoment

        return object_contact_momenten

    def retrieve_objectcontactmomenten_for_contactmoment(
        self, contactmoment: ContactMoment
    ) -> list[ObjectContactMoment]:
        response = self.get(
            "objectcontactmomenten", params={"contactmoment": contactmoment.url}
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data))
        return self.factory(ObjectContactMoment, all_data)

    #
    # klantcontactmomenten
    #
    @cache_result(
        "{self.base_url}:klantcontactmomenten:{klant_url}:{max_requests}",
        timeout=lambda self: self.cache_timeout,
    )
    def list_klantcontactmomenten_for_klant(
        self,
        klant_url: str,
        max_requests: int | None = DEFAULT_KLANTCONTACTMOMENTEN_MAX_REQUESTS,
    ) -> list[KlantContactMoment]:
        """List a klant's klantcontactmomenten, leaving `contactmoment` as a URL.

        Resolving those URLs is orchestrated by `eSuiteVragenService`, which fans the
        requests out over a worker pool. `klant` is left as the plain url too: nothing
        reads it back as an object, only the invariant check below compares against it.

        :param max_requests: caps the number of pagination requests followed, so a
        klant with a long history has a bounded worst case (e.g. during cache warm-up).
        The cache key varies on it, so every caller has to resolve it to the same
        value or they stop sharing an entry. That includes `invalidate()`, which has
        no listing to cap and so can only fall back on this default.
        """
        response = self.get(
            "klantcontactmomenten",
            params={"klant": klant_url},
        )
        self.raise_for_status(response)
        data = self.parse_json(response)
        all_data = list(pagination_helper(self, data, max_requests=max_requests))
        klanten_contact_moments = self.factory(KlantContactMoment, all_data)

        for kcm in klanten_contact_moments:
            if not kcm.klant == klant_url:
                raise ValueError("klantcontactmoment not linked to klant")

        return klanten_contact_moments

    def retrieve_objectcontactmomenten_for_object_type(
        self, contactmoment: ContactMoment, object_type: str
    ) -> list[ObjectContactMoment]:
        moments = self.retrieve_objectcontactmomenten_for_contactmoment(contactmoment)

        # eSuite doesn't implement a `object_type` query parameter
        return [moment for moment in moments if moment.object_type == object_type]

    def retrieve_objectcontactmoment(
        self, contactmoment: ContactMoment, object_type: str
    ) -> ObjectContactMoment | None:
        ocms = self.retrieve_objectcontactmomenten_for_object_type(
            contactmoment, object_type
        )
        if ocms:
            return ocms[0]


def _build_open_klant_client(type_) -> BaseAPIClient | None:
    config = ESuiteKlantConfig.get_solo()
    services_to_client_mapping = {
        "klanten": KlantenClient,
        "contactmomenten": ContactmomentenClient,
    }
    if client_class := services_to_client_mapping.get(type_):
        service = getattr(config, f"{type_}_service")
        if service:
            client_kwargs = {}
            if type_ == "contactmomenten":
                client_kwargs["cache_timeout"] = config.contactmoment_cache_timeout
            client = build_client(service, client_factory=client_class, **client_kwargs)
            return client

    logger.warning("no service defined for type", service_type=type_)
    return None


def build_contactmomenten_client() -> ContactmomentenClient | None:
    return _build_open_klant_client("contactmomenten")


def build_klanten_client() -> KlantenClient | None:
    return _build_open_klant_client("klanten")
