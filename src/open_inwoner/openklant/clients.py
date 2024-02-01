import logging
from typing import List, Optional

from ape_pie.client import APIClient
from requests.exceptions import RequestException
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import build_client as _build_client
from zgw_consumers.utils import pagination_helper

from open_inwoner.openzaak.cases import fetch_case_by_url_no_cache
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
    def create_klant(self, data: KlantCreateData) -> Optional[Klant]:
        try:
            response = self.post("klanten", json=data)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        klant = factory(Klant, data)

        return klant

    def retrieve_klant(
        self, user_bsn: Optional[str] = None, user_kvk_or_rsin: Optional[str] = None
    ) -> Optional[Klant]:
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

    def retrieve_klanten_for_bsn(self, user_bsn: str) -> List[Klant]:
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
    ) -> List[Klant]:
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

    def partial_update_klant(self, klant: Klant, update_data) -> Optional[Klant]:
        try:
            response = self.patch(url=klant.url, json=update_data)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        klant = factory(Klant, data)

        return klant


class ContactmomentenClient(APIClient):
    def create_contactmoment(
        self,
        data: ContactMomentCreateData,
        *,
        klant: Optional[Klant] = None,
        rol: Optional[str] = KlantContactRol.BELANGHEBBENDE,
    ) -> Optional[ContactMoment]:
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
                response = self.post(
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

    def retrieve_contactmoment(self, url) -> Optional[ContactMoment]:
        try:
            response = self.get(url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        contact_moment = factory(ContactMoment, data)

        return contact_moment

    def retrieve_objectcontactmomenten_for_contactmoment(
        self, contactmoment: ContactMoment
    ) -> List[ObjectContactMoment]:
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

        # resolve linked resources
        object_mapping = {}
        for ocm in object_contact_momenten:
            assert ocm.contactmoment == contactmoment.url
            ocm.contactmoment = contactmoment
            if ocm.object_type == "zaak":
                object_url = ocm.object
                # Avoid fetching the same object, if multiple relations wit the same object exist
                if ocm.object in object_mapping:
                    ocm.object = object_mapping[object_url]
                else:
                    ocm.object = fetch_case_by_url_no_cache(ocm.object)
                    object_mapping[object_url] = ocm.object

        return object_contact_momenten

    def retrieve_klantcontactmomenten_for_klant(
        self, klant: Klant
    ) -> List[KlantContactMoment]:
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
    ) -> List[ObjectContactMoment]:

        moments = self.retrieve_objectcontactmomenten_for_contactmoment(contactmoment)

        # eSuite doesn't implement a `object_type` query parameter
        ret = [moment for moment in moments if moment.object_type == object_type]

        return ret

    def retrieve_objectcontactmoment(
        self, contactmoment: ContactMoment, object_type: str
    ) -> Optional[ObjectContactMoment]:
        ocms = self.retrieve_objectcontactmomenten_for_object_type(
            contactmoment, object_type
        )
        if ocms:
            return ocms[0]


def build_client(type_) -> Optional[APIClient]:
    config = OpenKlantConfig.get_solo()
    services_to_client_mapping = {
        "klanten": KlantenClient,
        "contactmomenten": ContactmomentenClient,
    }
    if client_class := services_to_client_mapping.get(type_):
        service = getattr(config, f"{type_}_service")
        if service:
            client = _build_client(service, client_factory=client_class)
            return client

    logger.warning(f"no service defined for {type_}")
    return None
