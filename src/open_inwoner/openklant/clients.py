import logging

from ape_pie.client import APIClient
from requests.exceptions import RequestException
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import build_client
from zgw_consumers.utils import pagination_helper

from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.utils.api import ClientError, get_json_response

from .api_models import (
    ContactMoment,
    ContactMomentCreateData,
    Klant,
    KlantContactMoment,
    KlantContactRol,
    KlantCreateData,
    ObjectContactMoment,
)
from .models import OpenKlantConfig

logger = logging.getLogger(__name__)


class KlantenClient(APIClient):
    def create_klant(
        self,
        user_bsn: str | None = None,
        user_kvk_or_rsin: str | None = None,
        vestigingsnummer: str | None = None,
        data: KlantCreateData = None,
    ) -> Klant | None:
        if user_bsn:
            return self._create_klant_for_bsn(user_bsn)

        if user_kvk_or_rsin:
            return self._create_klant_for_kvk_or_rsin(
                user_kvk_or_rsin, vestigingsnummer=vestigingsnummer
            )

        try:
            response = self.post("klanten", json=data)
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception("exception while making request")
            return

        klant = factory(Klant, data)

        return klant

    def _create_klant_for_bsn(self, user_bsn: str) -> Klant:
        payload = {"subjectIdentificatie": {"inpBsn": user_bsn}}

        try:
            response = self.post("klanten", json=payload)
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception("exception while making request")
            return None

        klant = factory(Klant, data)

        return klant

    def _create_klant_for_kvk_or_rsin(
        self, user_kvk_or_rsin: str, *, vestigingsnummer=None
    ) -> list[Klant]:
        payload = {"subjectIdentificatie": {"innNnpId": user_kvk_or_rsin}}

        if vestigingsnummer:
            payload = {"subjectIdentificatie": {"vestigingsNummer": vestigingsnummer}}

        try:
            response = self.post(
                "klanten",
                json=payload,
            )
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception("exception while making request")
            return None

        klant = factory(Klant, data)

        return klant

    def retrieve_klant(
        self, user_bsn: str | None = None, user_kvk_or_rsin: str | None = None
    ) -> Klant | None:
        if not user_bsn and not user_kvk_or_rsin:
            return

        # this is technically a search operation and could return multiple records
        if user_bsn:
            klanten = self.retrieve_klanten_for_bsn(user_bsn)
        elif user_kvk_or_rsin:
            klanten = self.retrieve_klanten_for_kvk_or_rsin(user_kvk_or_rsin)

        if klanten:
            # let's use the first one
            return klanten[0]
        else:
            return

    def retrieve_klanten_for_bsn(self, user_bsn: str) -> list[Klant]:
        try:
            response = self.get(
                "klanten",
                params={"subjectNatuurlijkPersoon__inpBsn": user_bsn},
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        klanten = factory(Klant, all_data)

        return klanten

    def retrieve_klanten_for_kvk_or_rsin(
        self, user_kvk_or_rsin: str, *, vestigingsnummer=None
    ) -> list[Klant]:
        params = {"subjectNietNatuurlijkPersoon__innNnpId": user_kvk_or_rsin}

        if vestigingsnummer:
            params = {
                "subjectVestiging__vestigingsNummer": vestigingsnummer,
            }

        try:
            response = self.get(
                "klanten",
                params=params,
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        klanten = factory(Klant, all_data)

        return klanten

    def partial_update_klant(self, klant: Klant, update_data) -> Klant | None:
        try:
            response = self.patch(url=klant.url, json=update_data)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        klant = factory(Klant, data)

        return klant


class ContactmomentenClient(APIClient):
    #
    # contactmomenten
    #
    def create_contactmoment(
        self,
        data: ContactMomentCreateData,
        *,
        klant: Klant | None = None,
        rol: str | None = KlantContactRol.BELANGHEBBENDE,
    ) -> ContactMoment | None:
        try:
            response = self.post("contactmomenten", json=data)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        contactmoment = factory(ContactMoment, data)

        if klant:
            # relate contact to klant though a klantcontactmoment
            try:
                self.post(
                    "klantcontactmomenten",
                    json={
                        "klant": klant.url,
                        "contactmoment": contactmoment.url,
                        "rol": rol,
                    },
                )
            except (RequestException, ClientError) as e:
                logger.exception("exception while making request", exc_info=e)
                return

        return contactmoment

    def retrieve_contactmoment(self, url) -> ContactMoment | None:
        try:
            response = self.get(url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        contact_moment = factory(ContactMoment, data)

        return contact_moment

    #
    # objectcontactmomenten
    #
    def create_objectcontactmoment(
        self,
        contactmoment: ContactMoment,
        zaak: Zaak,
        object_type: str = "zaak",
    ) -> ObjectContactMoment | None:
        try:
            response = self.post(
                "objectcontactmomenten",
                json={
                    "contactmoment": contactmoment.url,
                    "object": zaak.url,
                    "objectType": object_type,
                },
            )
            data = get_json_response(response)
        except (RequestException, ClientError) as exc:
            logger.exception("exception while making request", exc_info=exc)
            return None

        object_contact_moment = factory(ObjectContactMoment, data)

        return object_contact_moment

    def retrieve_objectcontactmomenten_for_zaak(
        self, zaak: Zaak
    ) -> list[ObjectContactMoment]:
        try:
            response = self.get("objectcontactmomenten", params={"object": zaak.url})
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as exc:
            logger.exception("exception while making request", exc_info=exc)
            return []

        object_contact_momenten = factory(ObjectContactMoment, all_data)

        # resolve linked resources
        contactmoment_mapping = {}
        for ocm in object_contact_momenten:
            assert ocm.object == zaak.url
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
        try:
            response = self.get(
                "objectcontactmomenten", params={"contactmoment": contactmoment.url}
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        object_contact_momenten = factory(ObjectContactMoment, all_data)

        return object_contact_momenten

    #
    # klantcontactmomenten
    #
    def retrieve_klantcontactmomenten_for_klant(
        self, klant: Klant
    ) -> list[KlantContactMoment]:
        try:
            response = self.get(
                "klantcontactmomenten",
                params={"klant": klant.url},
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self, data))
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

        klanten_contact_moments = factory(KlantContactMoment, all_data)

        # resolve linked resources
        for kcm in klanten_contact_moments:
            assert kcm.klant == klant.url
            kcm.klant = klant
            kcm.contactmoment = self.retrieve_contactmoment(kcm.contactmoment)

        return klanten_contact_moments

    def retrieve_objectcontactmomenten_for_object_type(
        self, contactmoment: ContactMoment, object_type: str
    ) -> list[ObjectContactMoment]:

        moments = self.retrieve_objectcontactmomenten_for_contactmoment(contactmoment)

        # eSuite doesn't implement a `object_type` query parameter
        ret = [moment for moment in moments if moment.object_type == object_type]

        return ret

    def retrieve_objectcontactmoment(
        self, contactmoment: ContactMoment, object_type: str
    ) -> ObjectContactMoment | None:
        ocms = self.retrieve_objectcontactmomenten_for_object_type(
            contactmoment, object_type
        )
        if ocms:
            return ocms[0]


def _build_open_klant_client(type_) -> APIClient | None:
    config = OpenKlantConfig.get_solo()
    services_to_client_mapping = {
        "klanten": KlantenClient,
        "contactmomenten": ContactmomentenClient,
    }
    if client_class := services_to_client_mapping.get(type_):
        service = getattr(config, f"{type_}_service")
        if service:
            client = build_client(service, client_factory=client_class)
            return client

    logger.warning("no service defined for %s", type_)
    return None


def build_contactmomenten_client() -> ContactmomentenClient | None:
    return _build_open_klant_client("contactmomenten")


def build_klanten_client() -> KlantenClient | None:
    return _build_open_klant_client("klanten")
