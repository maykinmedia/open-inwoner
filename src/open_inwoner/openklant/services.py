import datetime
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import (
    Iterable,
    Literal,
    NotRequired,
    Protocol,
    Self,
    Sequence,
    assert_never,
    cast,
)

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import glom
import structlog
from ape_pie.client import APIClient
from pydantic import BaseModel, ConfigDict, TypeAdapter
from requests.exceptions import RequestException
from typing_extensions import TypedDict
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import build_client as build_zgw_client
from zgw_consumers.models.services import Service as ServiceConfig
from zgw_consumers.utils import pagination_helper

from open_inwoner.accounts.choices import NotificationChannelChoice
from open_inwoner.accounts.models import User
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.mijn_aanvragen.api_models import Zaak
from open_inwoner.mijn_aanvragen.clients import MultiZgwClientProxy
from open_inwoner.mijn_aanvragen.models import ZGWApiGroupConfig
from open_inwoner.openklant.api_models import (
    ContactMoment,
    ContactMomentCreateData,
    Klant,
    KlantContactMoment,
    KlantContactRol,
    KlantWritePayload,
    ObjectContactMoment,
)
from open_inwoner.openklant.constants import KlantenServiceType, Status
from open_inwoner.openklant.models import (
    ContactFormSubject,
    ESuiteKlantConfig,
    KlantContactMomentAnswer,
    OpenKlant2Config,
)
from open_inwoner.openklant.types import PartijUpdateData
from open_inwoner.openklant.wrap import (
    contactmoment_has_new_answer,
    fetch_klantcontactmoment,
    fetch_klantcontactmomenten,
    get_kcm_answer_mapping,
)
from open_inwoner.utils.api import ClientError, get_json_response
from open_inwoner.utils.logentry import system_action
from open_inwoner.utils.time import instance_is_new
from open_inwoner.utils.views import LogMixin
from openklant2.client import OpenKlant2Client
from openklant2.types.common import ForeignKeyRef
from openklant2.types.resources.betrokkene import (
    Betrokkene,
    BetrokkeneCreateData,
    CreateContactnaam,
)
from openklant2.types.resources.digitaal_adres import (
    DigitaalAdres,
    DigitaalAdresCreateData,
)
from openklant2.types.resources.interne_taak import InterneTaak
from openklant2.types.resources.klant_contact import (
    KlantContact,
    ListKlantContactParams,
)
from openklant2.types.resources.partij import (
    CreatePartijPersoonData,
    Partij,
    PartijListParams,
)
from openklant2.types.resources.partij_identificator import PartijIdentificator

logger = structlog.stdlib.get_logger(__name__)


class BsnFetchParam(TypedDict):
    user_bsn: str


class OrgFetchParam(TypedDict):
    user_kvk_or_rsin: str
    vestigingsnummer: NotRequired[str]


FetchParameters = BsnFetchParam | OrgFetchParam


@dataclass(frozen=True)
class ZaakWithApiGroup:
    zaak: Zaak
    api_group: ZGWApiGroupConfig


class Question(TypedDict):
    identification: str
    api_source_url: str  # points to contactmoment or klantcontact url
    api_source_uuid: uuid.UUID  # points to contactmoment or klantcontact uuid
    subject: str
    question_text: str
    answer_text: str | None
    registered_date: datetime.datetime
    status: str
    channel: str
    new_answer_available: bool
    api_service: KlantenServiceType


QuestionValidator = TypeAdapter(Question)


class KlantenService(Protocol):
    service_config: ServiceConfig

    def get_fetch_parameters(
        self,
        user: User | None = None,
    ) -> FetchParameters | None:
        """
        Determine the parameters used to perform Klanten/Contactmomenten fetches
        """
        if not user:
            return None

        if user.bsn:
            return {"user_bsn": user.bsn}
        elif user.kvk:
            kvk_or_rsin = user.kvk
            if getattr(self.config, "use_rsin_for_innNnpId_query_parameter", None):
                kvk_or_rsin = user.rsin

            if user.vestiging:
                return {
                    "user_kvk_or_rsin": kvk_or_rsin,
                    "vestigingsnummer": user.vestiging,
                }

            return {"user_kvk_or_rsin": kvk_or_rsin}

        return None


class eSuiteKlantenService(
    KlantenService,
):
    config: ESuiteKlantConfig
    client: APIClient
    service_config: ServiceConfig

    def __init__(self, config: ESuiteKlantConfig | None = None):
        self.config = cast(ESuiteKlantConfig, config or ESuiteKlantConfig.get_solo())
        if not self.config:
            raise ImproperlyConfigured(
                "eSuiteKlantenService instance needs a configuration"
            )

        if not self.config.klanten_service:
            raise ImproperlyConfigured(
                "eSuiteKlantenService instance needs a service configuration"
            )

        self.service_config = self.config.klanten_service
        self.client = build_zgw_client(
            service=self.service_config, client_factory=APIClient
        )
        if not self.client:
            raise ImproperlyConfigured("eSuiteKlantenService instance needs a client")

    def get_or_create_klant(
        self, fetch_params: FetchParameters, user: User
    ) -> tuple[Klant | None, bool]:
        if klant := self.retrieve_klant(**fetch_params):
            msg = "retrieved klant for user"
            created = False
        elif klant := self.create_klant(**fetch_params):
            msg = f"created klant ({klant.klantnummer}) for user"
            created = True
        else:
            return None, False

        system_action(msg, content_object=user)
        return klant, created

    def retrieve_klant(
        self,
        user_bsn: str | None = None,
        user_kvk_or_rsin: str | None = None,
        *,
        vestigingsnummer: str | None = None,
    ):
        klanten = None
        # this is technically a search operation and could return multiple records
        if user_bsn:
            klanten = self._retrieve_klanten_for_bsn(user_bsn)
        elif user_kvk_or_rsin:
            klanten = self._retrieve_klanten_for_kvk_or_rsin(
                user_kvk_or_rsin, vestigingsnummer=vestigingsnummer
            )

        return klanten[0] if klanten else None

    def _retrieve_klanten_for_bsn(self, user_bsn: str) -> list[Klant]:
        try:
            response = self.client.get(
                "klanten",
                params={"subjectNatuurlijkPersoon__inpBsn": user_bsn},
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self.client, data))
        except (RequestException, ClientError):
            logger.exception(
                "Failed to retrieve klanten for BSN",
                bsn=user_bsn,
            )
            return []

        klanten = factory(Klant, all_data)

        return klanten

    def _retrieve_klanten_for_kvk_or_rsin(
        self, user_kvk_or_rsin: str, *, vestigingsnummer=None
    ) -> list[Klant]:
        params = (
            {
                "subjectVestiging__vestigingsNummer": vestigingsnummer,
            }
            if vestigingsnummer
            else {
                "subjectNietNatuurlijkPersoon__innNnpId": user_kvk_or_rsin,
            }
        )

        try:
            response = self.client.get(
                "klanten",
                params=params,
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self.client, data))
        except (RequestException, ClientError):
            logger.exception(
                "Failed to retrieve klanten for eHerkenning user",
                user_kvk_or_rsin=user_kvk_or_rsin,
                vestigingsnummer=vestigingsnummer,
            )
            return []

        klanten = factory(Klant, all_data)

        return klanten

    def create_klant(
        self,
        user_bsn: str | None = None,
        user_kvk_or_rsin: str | None = None,
        vestigingsnummer: str | None = None,
        *,
        data: KlantWritePayload | None = None,
    ) -> Klant | None:
        if user_bsn and user_kvk_or_rsin:
            raise ValueError(
                "Specify either `user_bsn` or `user_kvk_or_rsin` with optional "
                "`vestigingsnummer`"
            )

        if vestigingsnummer and not user_kvk_or_rsin:
            raise ValueError(
                "You must specify `user_kvk_or_rsin` if `vestigingsnummer` is set"
            )

        payload = {}

        # Include writable attributes, if provided
        if data:
            payload.update(data)

        if user_bsn:
            payload = payload | {"subjectIdentificatie": {"inpBsn": user_bsn}}
        elif user_kvk_or_rsin:
            if vestigingsnummer:
                payload = payload | {
                    "subjectIdentificatie": {"vestigingsNummer": vestigingsnummer}
                }

            else:
                payload = payload | {
                    "subjectIdentificatie": {"innNnpId": user_kvk_or_rsin}
                }

        try:
            response = self.client.post("klanten", json=payload)
            response_data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception(
                "Failed to create klant for user",
                user_bsn=user_bsn,
                user_kvk_or_rsin=user_kvk_or_rsin,
            )
            return

        klant = factory(Klant, response_data)

        return klant

    def update_user_from_klant(self, klant: Klant, user: User):
        update_data = {}

        if (
            klant.emailadres
            and klant.emailadres != user.email
            and (not User.objects.filter(email__iexact=klant.emailadres).exists())
        ):
            update_data["email"] = klant.emailadres

        if klant.telefoonnummer and klant.telefoonnummer != user.phonenumber:
            update_data["phonenumber"] = klant.telefoonnummer

        if (
            klant.telefoonnummer_alternatief
            and klant.telefoonnummer_alternatief != user.phonenumber_alternative
        ):
            update_data["phonenumber_alternative"] = klant.telefoonnummer_alternatief

        config = SiteConfiguration.get_solo()
        if config.enable_notification_channel_choice:
            if (
                klant.toestemming_zaak_notificaties_alleen_digitaal is True
                and user.case_notification_channel
                != NotificationChannelChoice.digital_only
            ):
                update_data["case_notification_channel"] = (
                    NotificationChannelChoice.digital_only
                )

            elif (
                klant.toestemming_zaak_notificaties_alleen_digitaal is False
                and user.case_notification_channel
                != NotificationChannelChoice.digital_and_post
            ):
                update_data["case_notification_channel"] = (
                    NotificationChannelChoice.digital_and_post
                )
            else:
                # This is a guard against the scenario where a deployment is
                # configured to use an older version of the klanten backend (that
                # is, one that lacks the toestemmingZaakNotificatiesAlleenDigitaal
                # field). In such a scenario, the enable_notification_channel_choice
                # flag really shouldn't be set until the update has completed, but
                # we suspect this is rare. But to validate that assumption, we log
                # an error so we can remedy this in case we're wrong.
                logger.error(
                    "SiteConfig.enable_notification_channel_choice should not be set if"
                    " toestemmingZaakNotificatiesAlleenDigitaal is not available from the klanten backend"
                )

        if update_data:
            for attr, value in update_data.items():
                setattr(user, attr, value)
            user.save(update_fields=update_data.keys())

            system_action(
                f"updated user from klant API with fields: {', '.join(sorted(update_data.keys()))}",
                content_object=user,
            )

    def partial_update_klant(self, klant: Klant, update_data) -> Klant | None:
        try:
            response = self.client.patch(url=klant.url, json=update_data)
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception(
                "Failed to update klant",
                klant=klant,
            )
            return

        klant = factory(Klant, data)

        return klant

    def update_klant_from_user(
        self,
        klant: Klant,
        user: User,
        update_fields: (
            Sequence[
                Literal[
                    "telefoonnummer",
                    "telefoonnummerAlternatief",
                    "emailadres",
                    "toestemmingZaakNotificatiesAlleenDigitaal",
                ]
            ]
            | None
        ) = None,
    ):
        valid_update_fields = {
            "telefoonnummer",
            "telefoonnummerAlternatief",
            "emailadres",
            "toestemmingZaakNotificatiesAlleenDigitaal",
        }

        if update_fields:
            for field in update_fields:
                if field not in valid_update_fields:
                    raise ValueError(f"{field} is not a valid entry for update_fields")

        update_data: KlantWritePayload = {
            "emailadres": user.email or None,
            "telefoonnummer": user.phonenumber or None,
            "telefoonnummerAlternatief": user.phonenumber_alternative or None,
            "toestemmingZaakNotificatiesAlleenDigitaal": user.case_notification_channel
            == NotificationChannelChoice.digital_only,
        }

        the_keys = set(update_data.keys())
        if update_fields and set(update_fields) != valid_update_fields:
            for field in the_keys:
                if field not in update_fields:
                    del update_data[field]

        klant = self.partial_update_klant(klant, update_data)
        system_action(
            f"patched klant from user profile edit with fields: {', '.join(sorted(update_data.keys()))}",
            user=user,
        )
        return klant


class eSuiteVragenService(KlantenService):
    config: ESuiteKlantConfig

    def __init__(self, config: ESuiteKlantConfig | None = None):
        self.config = config or ESuiteKlantConfig.get_solo()
        if not self.config:
            raise ImproperlyConfigured(
                "eSuiteVragenService instance needs a configuration"
            )

        self.service_config = self.config.contactmomenten_service
        if not self.service_config:
            raise ImproperlyConfigured(
                "eSuiteVragenService instance needs a servivce configuration"
            )

        self.client = build_zgw_client(service=self.service_config)
        if not self.client:
            raise ImproperlyConfigured("eSuiteVragenService instance needs a client")

    #
    # contactmomenten
    #
    def retrieve_contactmoment(self, url) -> ContactMoment | None:
        try:
            response = self.client.get(url)
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception("exception while making request")
            return

        contact_moment = factory(ContactMoment, data)

        return contact_moment

    def create_contactmoment(
        self,
        data: ContactMomentCreateData,
        *,
        klant: Klant | None = None,
        rol: str | None = KlantContactRol.BELANGHEBBENDE,
    ) -> ContactMoment | None:
        try:
            response = self.client.post("contactmomenten", json=data)
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception(
                "Failed to create contactmoment",
                contactmoment_data=data,
            )
            return

        contactmoment = factory(ContactMoment, data)

        if klant:
            # relate contact to klant though a klantcontactmoment
            try:
                self.client.post(
                    "klantcontactmomenten",
                    json={
                        "klant": klant.url,
                        "contactmoment": contactmoment.url,
                        "verzendBevestigingsmail": self.config.send_klantcontact_confirmation_email,
                        "rol": rol,
                    },
                )
            except (RequestException, ClientError):
                logger.exception(
                    "Failed to create klantcontactmoment",
                    klant=klant,
                    contactmoment=contactmoment,
                )
                return

        return contactmoment

    #
    # objectcontactmomenten
    #
    def retrieve_objectcontactmoment(
        self, contactmoment: ContactMoment, object_type: str
    ) -> ObjectContactMoment | None:
        ocms = self.retrieve_objectcontactmomenten_for_object_type(
            contactmoment, object_type
        )
        if ocms:
            return ocms[0]

    def retrieve_objectcontactmomenten_for_object_type(
        self, contactmoment: ContactMoment, object_type: str
    ) -> list[ObjectContactMoment]:
        moments = self.retrieve_objectcontactmomenten_for_contactmoment(contactmoment)

        # eSuite doesn't implement a `object_type` query parameter
        ret = [moment for moment in moments if moment.object_type == object_type]

        return ret

    def create_objectcontactmoment(
        self,
        contactmoment: ContactMoment,
        zaak: Zaak,
        object_type: str = "zaak",
    ) -> ObjectContactMoment | None:
        try:
            response = self.client.post(
                "objectcontactmomenten",
                json={
                    "contactmoment": contactmoment.url,
                    "object": zaak.url,
                    "objectType": object_type,
                },
            )
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception(
                "Failed to create objectcontactmoment",
                zaak=zaak,
                contactmoment=contactmoment,
            )
            return None

        object_contact_moment = factory(ObjectContactMoment, data)

        return object_contact_moment

    def retrieve_objectcontactmomenten_for_zaak(
        self, zaak: Zaak
    ) -> list[ObjectContactMoment]:
        try:
            response = self.client.get(
                "objectcontactmomenten", params={"object": zaak.url}
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self.client, data))
        except (RequestException, ClientError):
            logger.exception(
                "Failed to retrieve objectcontactmoment for zaak",
                zaak=zaak,
            )
            return []

        object_contact_momenten = factory(ObjectContactMoment, all_data)

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
        try:
            response = self.client.get(
                "objectcontactmomenten", params={"contactmoment": contactmoment.url}
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self.client, data))
        except (RequestException, ClientError):
            logger.exception(
                "Failed to retrieve objectcontactmomenten for contactmoment",
                contactmoment=contactmoment,
            )
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
            response = self.client.get(
                "klantcontactmomenten",
                params={"klant": klant.url},
            )
            data = get_json_response(response)
            all_data = list(pagination_helper(self.client, data))
        except (RequestException, ClientError):
            logger.exception(
                "Failed to retrieve klantcontactmomenten for klant",
                klant=klant,
            )
            return []

        klanten_contact_moments = factory(KlantContactMoment, all_data)

        # resolve linked resources
        for kcm in klanten_contact_moments:
            if not kcm.klant == klant.url:
                raise ValueError("klantcontactmoment not linked to klant")

            kcm.klant = klant
            kcm.contactmoment = self.retrieve_contactmoment(kcm.contactmoment)

        return klanten_contact_moments

    @staticmethod
    def _get_kcm_subject(
        kcm: KlantContactMoment,
    ) -> str | None:
        """
        Determine the subject (`onderwerp`) of a `KlantContactMoment.contactmoment`:
            1. replace e-suite subject code with corresponding OIP configured subject or
            2. return the first OIP subject if multiple subjects are mapped to the same
               e-suite code or
            3. return the the e-suite subject code if no mapping exists
        """
        esuite_subject_code = getattr(kcm.contactmoment, "onderwerp", "")

        try:
            subject = ContactFormSubject.objects.get(
                esuite_subject_code=esuite_subject_code
            )
        except ContactFormSubject.MultipleObjectsReturned as exc:
            logger.warning(
                "Multiple OIP subjects mapped to the same e-suite subject code for contactmoment; using the first one",
                contactmoment_url=kcm.contactmoment.url,
                exc_info=True,
            )
            return ContactFormSubject.objects.first().subject
        except ContactFormSubject.DoesNotExist as exc:
            logger.warning(
                "Could not determine OIP subject for contactmoment; falling back on e-suite subject code ('onderwerp')",
                contactmoment_url=kcm.contactmoment.url,
                exc_info=True,
            )
            return esuite_subject_code

        return subject.subject

    def contactmoment_has_new_answer(
        self,
        contactmoment: ContactMoment,
        local_kcm_mapping: dict[str, KlantContactMomentAnswer] | None = None,
    ) -> bool:
        return contactmoment_has_new_answer(
            contactmoment,
            local_kcm_mapping,
        )

    @staticmethod
    def get_kcm_answer_mapping(
        contactmomenten: list[ContactMoment],
        user: User,
    ) -> dict[str, KlantContactMomentAnswer]:
        return get_kcm_answer_mapping(contactmomenten, user)

    def _build_question_dto(
        self,
        kcm: KlantContactMoment,
        local_kcm_mapping: dict[str, KlantContactMomentAnswer] | None = None,
    ) -> Question:
        if isinstance(kcm.contactmoment, str):
            raise ValueError("Received unresolved contactmoment")

        question_data = {
            "identification": kcm.contactmoment.identificatie,
            "url": reverse(
                "cases:contactmoment_detail",
                kwargs={
                    "api_service": KlantenServiceType.ESUITE.value,
                    "kcm_uuid": kcm.uuid,
                },
            ),
            "api_source_url": kcm.contactmoment.url,
            "api_source_uuid": kcm.contactmoment.uuid,
            "subject": self._get_kcm_subject(kcm) or "",
            "question_text": kcm.contactmoment.tekst,
            "answer_text": kcm.contactmoment.antwoord,
            "registered_date": datetime.datetime.fromisoformat(
                kcm.contactmoment.registratiedatum.isoformat()
            ),
            "status": str(Status.safe_label(kcm.contactmoment.status, _("Onbekend"))),
            "channel": kcm.contactmoment.kanaal,
            "new_answer_available": self.contactmoment_has_new_answer(
                kcm.contactmoment, local_kcm_mapping=local_kcm_mapping
            ),
            "api_service": KlantenServiceType.ESUITE,
        }
        return QuestionValidator.validate_python(question_data)

    def fetch_klantcontactmomenten(
        self,
        user_bsn: str | None = None,
        user_kvk_or_rsin: str | None = None,
        vestigingsnummer: str | None = None,
    ) -> list[KlantContactMoment]:
        return fetch_klantcontactmomenten(user_bsn, user_kvk_or_rsin, vestigingsnummer)

    def fetch_klantcontactmoment(
        self,
        kcm_uuid: str,
        user_bsn: str | None = None,
        user_kvk_or_rsin: str | None = None,
        vestigingsnummer: str | None = None,
    ) -> KlantContactMoment | None:
        return fetch_klantcontactmoment(
            kcm_uuid, user_bsn, user_kvk_or_rsin, vestigingsnummer
        )

    def list_questions(
        self, fetch_params: FetchParameters, user: User
    ) -> Iterable[Question]:
        kcms = self.fetch_klantcontactmomenten(**fetch_params)

        klant_config = ESuiteKlantConfig.get_solo()
        if exclude_range := klant_config.exclude_contactmoment_kanalen:
            kcms = [
                item
                for item in kcms
                if glom.glom(item, "contactmoment.kanaal") not in exclude_range
            ]

        contactmomenten = [
            self._build_question_dto(
                kcm,
                local_kcm_mapping=self.get_kcm_answer_mapping(
                    [kcm.contactmoment for kcm in kcms], user
                ),
            )
            for kcm in kcms
        ]
        return contactmomenten

    def retrieve_question(
        self, fetch_params: FetchParameters, question_uuid: str, user: User
    ) -> tuple[Question | None, ZaakWithApiGroup | None]:
        if not (kcm := self.fetch_klantcontactmoment(question_uuid, **fetch_params)):
            return None, None

        zaak_with_api_group: ZaakWithApiGroup | None = None
        ocm = self.retrieve_objectcontactmoment(kcm.contactmoment, "zaak")
        if ocm and ocm.object_type == "zaak":
            zaak_url = ocm.object
            groups = ZGWApiGroupConfig.objects.filter(
                klant_backend=KlantenServiceType.ESUITE.value
            )
            proxy = MultiZgwClientProxy([group.zaken_client for group in groups])
            proxy_response = proxy.fetch_zaak_by_url_no_cache(zaak_url)
            cases_found = proxy_response.truthy_responses
            if (case_count := len(cases_found)) == 0:
                logger.error(
                    "Unable to find matched contactmomenten zaak in any zgw backend"
                )
            else:
                if case_count > 1:
                    logger.error("Zaak found in multiple backends", zaak_url=zaak_url)

                zaak_with_api_group = next(
                    ZaakWithApiGroup(
                        zaak=zaak.result,
                        api_group=ZGWApiGroupConfig.objects.resolve_group_from_hints(
                            client=zaak.client
                        ),
                    )
                    for zaak in cases_found
                )

        return self._build_question_dto(kcm), zaak_with_api_group

    def list_questions_for_zaak(self, zaak: Zaak, user: User) -> list[Question]:
        # fetch klantcontactmomenten for filtering
        fetch_params = self.get_fetch_parameters(user)
        klantcontactmomenten = self.fetch_klantcontactmomenten(**fetch_params)
        relevant_contactmomenten_urls = {
            kcm.contactmoment.url for kcm in klantcontactmomenten
        }

        # fetch contactmomenten for zaak, filter out those not attched to a klant
        objectcontactmomenten = self.retrieve_objectcontactmomenten_for_zaak(zaak)
        contactmomenten: list[ContactMoment] = []
        for ocm in objectcontactmomenten:
            contactmoment: ContactMoment | None = getattr(ocm, "contactmoment", None)
            if contactmoment and contactmoment.url in relevant_contactmomenten_urls:
                contactmomenten.append(contactmoment)

        contactmomenten.sort(key=lambda q: q.registratiedatum, reverse=True)

        if exclude_range := self.config.exclude_contactmoment_kanalen:
            contactmomenten = [
                item
                for item in contactmomenten
                if glom.glom(item, "kanaal") not in exclude_range
            ]

        kcm_answer_mapping = get_kcm_answer_mapping(contactmomenten, user)
        questions: list[Question] = []
        for contactmoment in contactmomenten:
            new_answer_available = contactmoment_has_new_answer(
                contactmoment, kcm_answer_mapping
            )
            questions.append(
                dict(
                    identification=contactmoment.identificatie,
                    api_source_url=contactmoment.url,
                    api_source_uuid=contactmoment.uuid,
                    zaak_detail_url=zaak.url,
                    subject=contactmoment.onderwerp,
                    question_text=contactmoment.tekst,
                    answer_text=contactmoment.antwoord,
                    registered_date=contactmoment.registratiedatum,
                    status=contactmoment.status,
                    channel=contactmoment.kanaal,
                    new_answer_available=new_answer_available,
                    api_service=KlantenServiceType.ESUITE,
                )
            )

        return [QuestionValidator.validate_python(q) for q in questions]


@dataclass(frozen=True)
class OpenKlant2Answer:
    answer: str
    answer_kcm_uuid: str
    nummer: str
    plaatsgevonden_op: datetime.datetime

    # metadata
    viewed: bool = False

    @classmethod
    def from_klantcontact(cls, klantcontact: KlantContact) -> Self:
        if klantcontact["inhoud"] is None:
            raise ValueError("Klantcontact did not contain any content in `inhoud`")

        return cls(
            answer=klantcontact["inhoud"],
            answer_kcm_uuid=klantcontact["uuid"],
            nummer=klantcontact["nummer"],
            plaatsgevonden_op=datetime.datetime.fromisoformat(
                klantcontact["plaatsgevondenOp"]
            ),
        )


@dataclass(frozen=True)
class OpenKlant2Question(BaseModel):
    url: str
    question: str
    question_kcm_uuid: str
    onderwerp: str
    kanaal: str
    taal: str
    nummer: str
    plaatsgevonden_op: datetime.datetime

    answer: OpenKlant2Answer | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_klantcontact_and_answer(
        cls, klantcontact: KlantContact, answer: OpenKlant2Answer | None = None
    ) -> Self:
        if klantcontact["inhoud"] is None:
            raise ValueError("Klantcontact did not contain any content in `inhoud`")

        return cls(
            question=klantcontact["inhoud"],
            question_kcm_uuid=klantcontact["uuid"],
            onderwerp=klantcontact["onderwerp"],
            kanaal=klantcontact["kanaal"],
            taal=klantcontact["taal"],
            nummer=klantcontact["nummer"],
            plaatsgevonden_op=datetime.datetime.fromisoformat(
                klantcontact["plaatsgevondenOp"]
            ),
            answer=answer,
            url=klantcontact["url"],
        )


class OpenKlant2Service(
    LogMixin,
    KlantenService,
):
    config: OpenKlant2Config
    client: OpenKlant2Client

    def __init__(self, config: OpenKlant2Config | None = None):
        self.config = config or OpenKlant2Config.get_solo()
        if not self.config.service:
            raise ImproperlyConfigured("No openklant2 Service object configured")

        self.client = OpenKlant2Client(
            base_url=self.config.service.api_root,
            request_kwargs={
                "headers": {"Authorization": f"Token {self.config.service.secret}"}
            },
        )

        if mijn_vragen_actor := getattr(config, "mijn_vragen_actor", None):
            self.mijn_vragen_actor = (
                uuid.UUID(mijn_vragen_actor)
                if isinstance(mijn_vragen_actor, str)
                else mijn_vragen_actor
            )

    def find_partij_for_params(self, params: PartijListParams):
        resp = self.client.partij.list(params=params)

        if (count := resp["count"]) > 0:
            if count > 1:
                # TODO: Is this a use-case? The API seems to allow this
                logger.error("Multiple personen found in Openklant2 for a single BSN")

            return self.client.partij.retrieve(
                resp["results"][0]["uuid"],
                params={
                    "expand": [
                        "digitaleAdressen",
                        "betrokkenen",
                        "betrokkenen.hadKlantcontact",
                    ]
                },
            )

        return None

    @staticmethod
    def _bsn_list_param(bsn: str) -> PartijListParams:
        return {
            "partijIdentificator__codeSoortObjectId": "bsn",
            "partijIdentificator__codeRegister": "brp",
            "partijIdentificator__codeObjecttype": "natuurlijk_persoon",
            "partijIdentificator__objectId": bsn,
            "soortPartij": "persoon",
        }

    @staticmethod
    def _kvk_list_param(kvk: str) -> PartijListParams:
        return {
            "partijIdentificator__codeSoortObjectId": "kvk_nummer",
            "partijIdentificator__codeRegister": "hr",
            "partijIdentificator__codeObjecttype": "niet_natuurlijk_persoon",
            "partijIdentificator__objectId": kvk,
            "soortPartij": "organisatie",
        }

    def find_persoon_for_bsn(self, bsn: str) -> Partij | None:
        return self.find_partij_for_params(params=self._bsn_list_param(bsn))

    def find_organisatie_for_kvk_and_vestiging(
        self,
        *,
        kvk: str,
        vestigingsnummer: str | None = None,
    ) -> Partij | None:
        parent_kvk_results = list(
            self.client.partij_identificator.list_iter(
                params={
                    "partijIdentificatorCodeSoortObjectId": "kvk_nummer",
                    "partijIdentificatorCodeRegister": "hr",
                    "partijIdentificatorCodeObjecttype": "niet_natuurlijk_persoon",
                    "partijIdentificatorObjectId": kvk,
                }
            )
        )
        if not parent_kvk_results:
            return None

        kvk_pi: PartijIdentificator
        kvk_pi_count = len(parent_kvk_results)

        if kvk_pi_count == 0:
            return None

        kvk_pi = parent_kvk_results[0]
        if kvk_pi_count > 1:
            logger.error(
                "Unexpectedly found Partij Identificatoren for single kvk, defaulting to first option",
                pi_count=kvk_pi_count,
                kvk=kvk,
                selected_uuid=kvk_pi["uuid"],
            )

        # Return the kvk partij if no vestiging
        if not vestigingsnummer:
            if not (kvk_partij_ref := kvk_pi["identificeerdePartij"]):
                # The PI exists, but not a Partij for the legal entity
                return None

            return self.client.partij.retrieve(kvk_partij_ref["uuid"])

        # Bit convoluted: find all PIs for a vestiging, then cross-reference to the kvk
        # pi for the parent
        vestiging_pi = next(
            result
            for result in self.client.partij_identificator.list_iter(
                params={
                    "partijIdentificatorCodeSoortObjectId": "vestigingsnummer",
                    "partijIdentificatorCodeRegister": "hr",
                    "partijIdentificatorCodeObjecttype": "vestiging",
                    "partijIdentificatorObjectId": vestigingsnummer,
                }
            )
            if result["subIdentificatorVan"]
            and result["subIdentificatorVan"]["uuid"] == kvk_pi["uuid"]
        )

        if not vestiging_pi:
            return None

        if not vestiging_pi["identificeerdePartij"]:
            logger.warning(
                "Found a Partij Identificator for vestiging without a linked Partij",
                object_id=vestiging_pi["partijIdentificator"]["objectId"],
            )
            return None

        return self.client.partij.retrieve(vestiging_pi["identificeerdePartij"]["uuid"])

    def get_partij_for_user(self, user: User) -> Partij | None:
        if user.kvk:
            return self.find_organisatie_for_kvk_and_vestiging(
                kvk=user.kvk,
                vestigingsnummer=user.vestiging,
            )

        if user.bsn:
            return self.find_persoon_for_bsn(user.bsn)

        return None

    def get_or_create_partij_for_user(self, user: User) -> tuple[Partij | None, bool]:
        partij = None
        created = False

        if user.kvk:
            # User has KVK, create/find organisatie
            organisatie = self.find_organisatie_for_kvk_and_vestiging(
                kvk=user.kvk,
                vestigingsnummer=user.vestiging,
            )

            if not organisatie:
                organisatie = self.client.partij.create_organisatie(
                    data={
                        "digitaleAdressen": None,
                        "voorkeursDigitaalAdres": None,
                        "rekeningnummers": None,
                        "voorkeursRekeningnummer": None,
                        "indicatieGeheimhouding": False,
                        "indicatieActief": True,
                        "voorkeurstaal": "nld",
                        "soortPartij": "organisatie",
                        "partijIdentificatie": {
                            "naam": user.company_name,
                        },
                    }
                )
                created = True

                try:
                    try:
                        # Check for an existing entity-only PI (e.g. where
                        # subIdentificatorVan is not set)
                        kvk_pi = next(
                            pi
                            for pi in self.client.partij_identificator.list_iter(
                                params={
                                    "partijIdentificatorCodeSoortObjectId": "kvk_nummer",
                                    "partijIdentificatorCodeRegister": "hr",
                                    "partijIdentificatorCodeObjecttype": "niet_natuurlijk_persoon",
                                    "partijIdentificatorObjectId": user.kvk,
                                }
                            )
                            if not pi["subIdentificatorVan"]
                        )
                    except StopIteration:
                        kvk_pi = self.client.partij_identificator.create(
                            data={
                                "identificeerdePartij": {"uuid": organisatie["uuid"]},
                                "partijIdentificator": {
                                    "codeObjecttype": "niet_natuurlijk_persoon",
                                    "codeSoortObjectId": "kvk_nummer",
                                    "objectId": user.kvk,
                                    "codeRegister": "hr",
                                },
                            }
                        )

                    if user.vestiging:
                        try:
                            next(
                                pi
                                for pi in self.client.partij_identificator.list_iter(
                                    params={
                                        "partijIdentificatorCodeSoortObjectId": "vestigingsnummer",
                                        "partijIdentificatorCodeRegister": "hr",
                                        "partijIdentificatorCodeObjecttype": "vestiging",
                                        "partijIdentificatorObjectId": user.vestiging,
                                    }
                                )
                                if pi["subIdentificatorVan"]
                                and pi["subIdentificatorVan"]["uuid"] == kvk_pi["uuid"]
                            )
                        except StopIteration:
                            self.client.partij_identificator.create(
                                data={
                                    "identificeerdePartij": {
                                        "uuid": organisatie["uuid"]
                                    },
                                    "subIdentificatorVan": {
                                        "uuid": kvk_pi["uuid"],
                                    },
                                    "partijIdentificator": {
                                        "codeObjecttype": "vestiging",
                                        "codeSoortObjectId": "vestigingsnummer",
                                        "objectId": user.vestiging,
                                        "codeRegister": "hr",
                                    },
                                }
                            )
                except Exception:
                    logger.exception("Unable to register identificatoren for partij")

            partij = organisatie

        else:
            # No KVK, always create/find persoon (regardless of BSN)
            if user.bsn:  # noqa: SIM108
                # Try to find existing persoon by BSN
                persoon = self.find_persoon_for_bsn(user.bsn)
            else:
                # No BSN, can't find existing persoon
                persoon = None

            if not persoon:
                # Create new persoon
                partij_data = {
                    "digitaleAdressen": None,
                    "voorkeursDigitaalAdres": None,
                    "rekeningnummers": None,
                    "voorkeursRekeningnummer": None,
                    "indicatieGeheimhouding": False,
                    "indicatieActief": True,
                    "voorkeurstaal": "nld",
                    "soortPartij": "persoon",
                    "partijIdentificatie": {
                        "contactnaam": {
                            "voornaam": user.first_name,
                            "achternaam": user.last_name,
                            "voorletters": "",
                            "voorvoegselAchternaam": "",
                        },
                    },
                }

                # Only add identificatoren if user has BSN
                if user.bsn:
                    partij_data["partijIdentificatoren"] = [
                        {
                            "partijIdentificator": {
                                "codeObjecttype": "natuurlijk_persoon",
                                "codeSoortObjectId": "bsn",
                                "objectId": user.bsn,
                                "codeRegister": "brp",
                            }
                        }
                    ]

                persoon = self.client.partij.create_persoon(
                    data=cast(CreatePartijPersoonData, partij_data)
                )
                created = True

            partij = persoon

        msg = (
            f"{'created' if created else 'retrieved'} partij {partij['uuid']} for user"
        )
        system_action(msg, content_object=user)

        return partij, created

    def _retrieve_digitale_addressen(
        self,
        subject_type: Literal["partij", "betrokkene"],
        uuid: str,
    ) -> list[DigitaalAdres]:
        if subject_type == "partij":
            paginated_data = self.client.digitaal_adres.list(
                params={"verstrektDoorPartij__uuid": uuid}
            )
        else:
            paginated_data = self.client.digitaal_adres.list(
                params={"verstrektDoorBetrokkene__uuid": uuid}
            )

        digitale_adressen = list(pagination_helper(self.client, paginated_data))

        return digitale_adressen

    def retrieve_digitale_addressen_for_partij(
        self, partij_uuid: str
    ) -> list[DigitaalAdres]:
        return self._retrieve_digitale_addressen("partij", uuid=partij_uuid)

    def retrieve_digitale_addressen_for_betrokkene(
        self, betrokkene_uuid: str
    ) -> list[DigitaalAdres]:
        return self._retrieve_digitale_addressen("betrokkene", uuid=betrokkene_uuid)

    def _filter_digitale_addressen(
        self,
        subject_type: Literal["partij", "betrokkene"],
        uuid: str,
        *,
        soort_digital_adres: Literal["email", "telefoonnummer"],
        adressen: Iterable[DigitaalAdres] | None = None,
    ) -> list[DigitaalAdres]:
        if adressen is None:
            match subject_type:
                case "partij":
                    adressen = self.retrieve_digitale_addressen_for_partij(uuid)
                case "betrokkene":
                    adressen = self.retrieve_digitale_addressen_for_betrokkene(uuid)
                case _:
                    assert_never(subject_type)

        return [
            digitaal_adres
            for digitaal_adres in adressen
            if digitaal_adres["soortDigitaalAdres"] == soort_digital_adres
        ]

    def filter_digitale_addressen_for_partij(
        self,
        partij_uuid: str,
        *,
        soort_digital_adres: Literal["email", "telefoonnummer"],
        adressen: Iterable[DigitaalAdres] | None = None,
    ) -> list[DigitaalAdres]:
        return self._filter_digitale_addressen(
            "partij",
            uuid=partij_uuid,
            soort_digital_adres=soort_digital_adres,
            adressen=adressen,
        )

    def filter_digitale_addressen_for_betrokkene(
        self,
        betrokkene_uuid: str,
        *,
        soort_digital_adres: Literal["email", "telefoonnummer"],
        adressen: Iterable[DigitaalAdres] | None = None,
    ) -> list[DigitaalAdres]:
        return self._filter_digitale_addressen(
            "betrokkene",
            uuid=betrokkene_uuid,
            soort_digital_adres=soort_digital_adres,
            adressen=adressen,
        )

    def _get_or_create_digitaal_adres(
        self,
        subject_type: Literal["partij", "betrokkene"],
        uuid: str,
        soort_adres: Literal["email", "telefoonnummer"],
        adres: str,
        is_standaard_adres: bool = False,
    ) -> tuple[DigitaalAdres, bool]:
        digitale_adressen = self._filter_digitale_addressen(
            subject_type=subject_type,
            uuid=uuid,
            soort_digital_adres=soort_adres,
        )
        for digitaal_adres in digitale_adressen:
            if (
                digitaal_adres["adres"] == adres
                and digitaal_adres["isStandaardAdres"] == is_standaard_adres
            ):
                return digitaal_adres, False

        if subject_type == "partij":
            adres_data = DigitaalAdresCreateData(
                adres=adres,
                soortDigitaalAdres=soort_adres,
                isStandaardAdres=is_standaard_adres,
                omschrijving="OIP profiel",
                verstrektDoorPartij={"uuid": uuid},
                verstrektDoorBetrokkene=None,
            )
        else:
            adres_data = DigitaalAdresCreateData(
                adres=adres,
                soortDigitaalAdres=soort_adres,
                isStandaardAdres=is_standaard_adres,
                omschrijving="OIP profiel",
                verstrektDoorBetrokkene={"uuid": uuid},
                verstrektDoorPartij=None,
            )

        return self.client.digitaal_adres.create(data=adres_data), True

    def get_or_create_digitaal_adres_for_partij(
        self,
        partij_uuid: str,
        soort_adres: Literal["email", "telefoonnummer"],
        adres: str,
        is_standaard_adres: bool = False,
    ) -> tuple[DigitaalAdres, bool]:
        return self._get_or_create_digitaal_adres(
            "partij",
            uuid=partij_uuid,
            soort_adres=soort_adres,
            adres=adres,
            is_standaard_adres=is_standaard_adres,
        )

    def get_or_create_digitaal_adres_for_betrokkene(
        self,
        betrokkene_uuid: str,
        soort_adres: Literal["email", "telefoonnummer"],
        adres: str,
        is_standaard_adres: bool = False,
    ) -> tuple[DigitaalAdres, bool]:
        return self._get_or_create_digitaal_adres(
            "betrokkene",
            uuid=betrokkene_uuid,
            soort_adres=soort_adres,
            adres=adres,
            is_standaard_adres=is_standaard_adres,
        )

    def update_user_from_partij(self, partij_uuid: str, user: User):
        update_data = {}

        adressen = self.retrieve_digitale_addressen_for_partij(partij_uuid)

        if email_adressen := self.filter_digitale_addressen_for_partij(
            partij_uuid, soort_digital_adres="email", adressen=adressen
        ):
            email = email_adressen[0]["adres"]
            if not User.objects.filter(email__iexact=email).exists():
                update_data["email"] = email

        if phone_adressen := self.filter_digitale_addressen_for_partij(
            partij_uuid, soort_digital_adres="telefoonnummer", adressen=adressen
        ):
            for adres in phone_adressen:
                if adres["isStandaardAdres"]:
                    update_data["phonenumber"] = adres["adres"]
                else:
                    update_data["phonenumber_alternative"] = adres["adres"]

            # we currently only support two phone numbers: primary + secondary
            # the following edge case cannot happen through OIP, but we cannot
            # exclude that it happens through some external service. In this case,
            # we pick the last one
            if len(phone_adressen) > 2:
                logger.warning(
                    "More than two phone numbers found for partij",
                    partij_uuid=partij_uuid,
                )

        if update_data:
            for attr, value in update_data.items():
                setattr(user, attr, value)
            user.save(update_fields=update_data.keys())

            system_action(
                f"updated user from klant API with fields: {', '.join(sorted(update_data.keys()))}",
                content_object=user,
            )

    def update_partij_from_user_data(
        self,
        partij_uuid: str,
        update_data: PartijUpdateData,
    ) -> list[str]:
        updated_fields: list[str] = []

        if phonenumber := update_data.get("phonenumber"):
            _, created = self.get_or_create_digitaal_adres_for_partij(
                partij_uuid=partij_uuid,
                soort_adres="telefoonnummer",
                adres=phonenumber,
                is_standaard_adres=True,
            )
            if created:
                updated_fields.append("digitaleAddresen.telefoonnummer")

        for attr, soort_adres in (
            ("email", "email"),
            ("phonenumber_alternative", "telefoonnummer"),
        ):
            if adres := update_data.get(attr):
                _, created = self.get_or_create_digitaal_adres_for_partij(
                    partij_uuid=partij_uuid,
                    soort_adres=cast(Literal["email", "telefoonnummer"], soort_adres),
                    adres=adres,
                    is_standaard_adres=False,
                )
                if created:
                    updated_fields.append(f"digitaleAddresen.{soort_adres}")

        if updated_fields:
            system_action(
                f"updated Partij {partij_uuid} with fields: {', '.join(sorted(updated_fields))}",
            )

        return updated_fields

    def _create_klantcontact(
        self,
        question: str,
        subject: str,
    ) -> KlantContact:
        if len(question.rstrip()) == 0:
            raise ValueError("You must provide a question")
        if not self.config.mijn_vragen_actor:
            raise RuntimeError(
                "You must define an actor to whom the question will be assigned. "
                "Initialize the service with a value for `mijn_vragen_actor`."
            )

        klantcontact = self.client.klant_contact.create(
            data={
                "inhoud": question,
                "onderwerp": subject,
                "taal": "nld",
                "kanaal": self.config.mijn_vragen_kanaal,
                "vertrouwelijk": False,
                "plaatsgevondenOp": timezone.now().isoformat(),
            }
        )
        logger.info("Created klantcontact", klantcontact_uuid=klantcontact["uuid"])

        return klantcontact

    def _create_betrokkene_in_klantcontact(
        self,
        klantcontact_uuid: str,
        was_partij: ForeignKeyRef | None,
        contactnaam: CreateContactnaam | None,
    ) -> Betrokkene:
        data = BetrokkeneCreateData(
            wasPartij=was_partij,
            rol="klant",
            hadKlantcontact={"uuid": klantcontact_uuid},
            organisatienaam="Open Inwoner Platform",
            initiator=True,
            contactnaam=contactnaam,
        )
        betrokkene = self.client.betrokkene.create(data=data)

        logger.info("Created betrokkene", betrokkene_uuid=betrokkene["uuid"])

        return betrokkene

    def _create_interne_taak(
        self,
        klantcontact_uuid: str,
    ) -> InterneTaak:
        if not self.config.mijn_vragen_actor:
            raise RuntimeError("unexpected error: mijn_vragen_actor not configured")

        taak = self.client.interne_taak.create(
            data={
                "aanleidinggevendKlantcontact": {"uuid": klantcontact_uuid},
                "toelichting": "Beantwoorden vraag",
                "gevraagdeHandeling": "Vraag beantwoorden in aanleiding gevend klant contact",
                "status": "te_verwerken",
                "toegewezenAanActor": {"uuid": str(self.config.mijn_vragen_actor)},
            }
        )
        logger.info("Created taak", taak_uuid=taak["uuid"])

        return taak

    def create_question_for_partij(
        self,
        partij_uuid: str,
        question: str,
        subject: str,
    ) -> OpenKlant2Question:
        klantcontact = self._create_klantcontact(question=question, subject=subject)
        self._create_betrokkene_in_klantcontact(
            klantcontact_uuid=klantcontact["uuid"],
            was_partij={"uuid": partij_uuid},
            contactnaam=None,
        )
        self._create_interne_taak(klantcontact_uuid=klantcontact["uuid"])

        return OpenKlant2Question.from_klantcontact_and_answer(klantcontact)

    def create_question_with_betrokkene(
        self,
        question: str,
        subject: str,
        first_name: str,
        last_name: str,
        email: str,
        phonenumber: str,
    ) -> OpenKlant2Question:
        klantcontact = self._create_klantcontact(question=question, subject=subject)
        betrokkene = self._create_betrokkene_in_klantcontact(
            klantcontact_uuid=klantcontact["uuid"],
            was_partij=None,
            contactnaam=CreateContactnaam(voornaam=first_name, achternaam=last_name),
        )

        if email:
            self.get_or_create_digitaal_adres_for_betrokkene(
                betrokkene_uuid=betrokkene["uuid"],
                soort_adres="email",
                adres=email,
            )
        if phonenumber:
            self.get_or_create_digitaal_adres_for_betrokkene(
                betrokkene_uuid=betrokkene["uuid"],
                soort_adres="telefoonnummer",
                adres=phonenumber,
            )

        self._create_interne_taak(klantcontact_uuid=klantcontact["uuid"])

        return OpenKlant2Question.from_klantcontact_and_answer(klantcontact)

    def create_question_for_zaak(
        self,
        partij_uuid: str,
        question: str,
        zaak: Zaak,
    ) -> OpenKlant2Question:
        ok2_question = self.create_question_for_partij(
            partij_uuid=partij_uuid,
            question=question,
            subject=f"Vraag voor zaak: {zaak.identificatie}",
        )

        self.log_system_action(
            "registered question {question_uuid} for partij {partij} via OpenKlant".format(
                question_uuid=ok2_question.question_kcm_uuid, partij=partij_uuid
            )
        )

        # TODO: No convention has (yet) been established for the use of
        # `onderwerpobjectidentificator`; the implementation is provisianal
        onderwerp_object = self.client.onderwerp_object.create(
            data={
                "klantcontact": {"uuid": ok2_question.question_kcm_uuid},
                "wasKlantcontact": None,
                "onderwerpobjectidentificator": {
                    "objectId": zaak.identificatie,
                    "codeObjecttype": "zaak",
                    "codeRegister": "openzaak",
                    "codeSoortObjectId": "identificatie",
                },
            }
        )
        self.log_system_action(
            "Created onderwerp_object {onderwerp_object_uuid} for zaak `{zaak_identificatie}`".format(
                onderwerp_object_uuid=onderwerp_object["uuid"],
                zaak_identificatie=zaak.identificatie,
            )
        )

        return ok2_question

    def create_answer(
        self, partij_uuid: str, question_klantcontact_uuid: str, answer: str
    ) -> OpenKlant2Answer:
        """Create an answer for a question identified through `question_klantcontact_uuid`.

        Note that this method is mainly for documentation and testing. In practice, answers will be
        created by other systems (e.g. the customer support software at the municipality).
        """
        question_klantcontact = self.client.klant_contact.retrieve(
            question_klantcontact_uuid
        )
        answer_klantcontact = self.client.klant_contact.create(
            data={
                "inhoud": answer,
                "onderwerp": question_klantcontact["onderwerp"],
                "taal": "nld",
                "kanaal": self.config.mijn_vragen_kanaal,
                "vertrouwelijk": False,
                "plaatsgevondenOp": timezone.now().isoformat(),
            }
        )

        self.client.betrokkene.create(
            data={
                "rol": "klant",
                "hadKlantcontact": {"uuid": answer_klantcontact["uuid"]},
                "initiator": True,
                "wasPartij": {"uuid": partij_uuid},
                "organisatienaam": "Open Inwoner Platform",
            }
        )

        self.client.onderwerp_object.create(
            data={
                "klantcontact": {
                    "uuid": answer_klantcontact["uuid"],
                },
                "wasKlantcontact": {
                    "uuid": question_klantcontact["uuid"],
                },
            }
        )

        return OpenKlant2Answer.from_klantcontact(answer_klantcontact)

    def klantcontacten_for_partij(
        self, partij_uuid: str, *, kanaal: str | None = None
    ) -> Iterable[KlantContact]:
        # There is currently no good way to filter the klantcontacten by a
        # Partij (see https://github.com/maykinmedia/open-klant/issues/256). So
        # unfortunately, we have to fetch all rows and do the filtering client
        # side.
        params: ListKlantContactParams = {
            "expand": [
                "leiddeTotInterneTaken",
                "gingOverOnderwerpobjecten",
                "hadBetrokkenen",
                "hadBetrokkenen.wasPartij",
            ],
            "kanaal": kanaal or self.config.mijn_vragen_kanaal,
        }
        klantcontacten = self.client.klant_contact.list_iter(params=params)
        klantcontacten_for_partij = filter(
            lambda row: partij_uuid
            in glom.glom(
                row,
                (
                    "_expand.hadBetrokkenen",
                    [(glom.Coalesce("wasPartij.uuid", default=glom.SKIP),)],
                ),
            ),
            klantcontacten,
        )

        # only show questions initiated by the current user
        klantcontacten_for_initiator = filter(
            lambda row: True
            in glom.glom(
                row,
                ("_expand.hadBetrokkenen", ["initiator"]),
            ),
            klantcontacten_for_partij,
        )

        return klantcontacten_for_initiator

    def questions_for_partij(self, partij_uuid: str) -> list[OpenKlant2Question]:
        answers_for_klantcontact_uuid = {}
        question_uuids = []
        klantcontact_uuid_to_klantcontact_object = {}
        for klantcontact in self.klantcontacten_for_partij(
            partij_uuid, kanaal=self.config.mijn_vragen_kanaal
        ):
            klantcontact_uuid_to_klantcontact_object[klantcontact["uuid"]] = (
                klantcontact
            )

            if onderwerp_objecten := klantcontact["gingOverOnderwerpobjecten"]:
                # Determine if the klantcontact is an answer by checking `wasKlantcontact` in
                # the related onderwerp_object; otherwise, treat it as question
                #
                # TODO: is it sufficient to pick the first onderwerp_object?
                # TODO: our use of `onderwerp_object` to model the relation of a klantcontact
                # to different kinds of objects like answers, zaken etc. needs to be
                # revisited
                answer_onderwerp_object = self.client.onderwerp_object.retrieve(
                    onderwerp_objecten[0]["uuid"]
                )
                if not answer_onderwerp_object["wasKlantcontact"]:
                    question_uuids.append(klantcontact["uuid"])
                    continue

                # Map the question to the answer
                question_uuid = answer_onderwerp_object["wasKlantcontact"]["uuid"]
                answers_for_klantcontact_uuid[question_uuid] = klantcontact["uuid"]
            else:
                # No onderwerp object, so we treat this klantcontact as a question
                question_uuids.append(klantcontact["uuid"])

        question_objs: list[OpenKlant2Question] = []
        for question_uuid in question_uuids:
            question = klantcontact_uuid_to_klantcontact_object[question_uuid]
            try:
                answer_uuid = answers_for_klantcontact_uuid[question_uuid]
                answer = klantcontact_uuid_to_klantcontact_object[answer_uuid]
            except KeyError:
                answer = None

            answer_obj = None
            if answer:
                answer_obj = OpenKlant2Answer.from_klantcontact(answer)

            question_objs.append(
                OpenKlant2Question.from_klantcontact_and_answer(question, answer_obj)
            )

        question_objs.sort(key=lambda o: o.plaatsgevonden_op)
        return question_objs

    def list_questions(
        self, fetch_params: FetchParameters, user: User
    ) -> list[Question]:
        partij, _ = self.get_or_create_partij_for_user(user)
        if not partij:
            # Will be logged by get_or_create_partij_for_user
            return []

        questions = self.questions_for_partij(partij_uuid=partij["uuid"])
        return self._build_question_dtos(questions, user)

    def retrieve_question(
        self,
        fetch_params: FetchParameters,
        question_uuid: str,
        user: User,
    ) -> tuple[Question | None, ZaakWithApiGroup | None]:
        if bsn := fetch_params.get("user_bsn"):
            partij = self.find_persoon_for_bsn(str(bsn))
        elif kvk_or_rsin := fetch_params.get("user_kvk_or_rsin"):
            partij = self.find_organisatie_for_kvk_and_vestiging(kvk=kvk_or_rsin)

        if not partij:
            return (None, None)

        all_questions = self.questions_for_partij(partij_uuid=partij["uuid"])
        question = next(
            q for q in all_questions if q.question_kcm_uuid == question_uuid
        )

        # fetch onderwerp_object linked to klantcontact
        onderwerp_objecten = [
            obj
            for obj in self.client.onderwerp_object.list()["results"]
            if obj["klantcontact"]
            and obj["klantcontact"]["uuid"] == question.question_kcm_uuid
        ]
        if not onderwerp_objecten:
            return self._build_question_dto(question_ok2=question, user=user), None
        if len(onderwerp_objecten) > 1:
            logger.error(
                "More than one onderwerp_object found for question",
                question_uuid=question.question_kcm_uuid,
            )
            return self._build_question_dto(question_ok2=question, user=user), None

        onderwerp_object = onderwerp_objecten[0]

        # fetch zaken for user
        groups = ZGWApiGroupConfig.objects.filter(
            klant_backend=KlantenServiceType.OPENKLANT2.value
        )
        proxy = MultiZgwClientProxy([group.zaken_client for group in groups])
        proxy_response = proxy.fetch_zaken(user_bsn=user.bsn)

        if not (truthy_responses := proxy_response.truthy_responses):
            logger.info(
                "Unable to find matched contactmomenten zaak with OpenKlant2 backend"
            )
            return self._build_question_dto(question_ok2=question, user=user), None

        # find the unique zaak + relevant api client for the question
        zaken_for_question: list = []
        clients = []
        for response in truthy_responses:
            # discard the client for determining the api_group; we only need the zaak
            zaken = response.result
            client = response.client
            zaken_filtered = filter(
                lambda z: z.identificatie
                == onderwerp_object["onderwerpobjectidentificator"]["objectId"],
                zaken,
            )
            zaken_for_question.extend(zaken_filtered)
            clients.append(client)

        # sanity checks
        if not zaken_for_question:
            logger.info(
                "Could not find zaak corresponding to question",
                question_kcm_uuid=question.question_kcm_uuid,
            )
            return self._build_question_dto(question_ok2=question, user=user), None
        if len(zaken_for_question) > 1:
            logger.error(
                "More than one zaak found for question",
                question_uuid=question.question_kcm_uuid,
            )
            return self._build_question_dto(question_ok2=question, user=user), None
        if len(clients) > 1:
            logger.error("Found one zaak in multiple backends")
            return self._build_question_dto(question_ok2=question, user=user), None

        group = ZGWApiGroupConfig.objects.resolve_group_from_hints(client=clients[0])
        zaak_with_api_group = ZaakWithApiGroup(
            zaak=zaken_for_question[0], api_group=group
        )

        return (
            self._build_question_dto(question_ok2=question, user=user),
            zaak_with_api_group,
        )

    def _build_question_dtos(
        self,
        questions_ok2: list[OpenKlant2Question],
        user: User,
    ) -> list[Question]:
        return [
            self._build_question_dto(question, user=user) for question in questions_ok2
        ]

    def _build_question_dto(
        self,
        question_ok2: OpenKlant2Question,
        user: User,
    ) -> Question:
        answer_metadata, _ = KlantContactMomentAnswer.objects.get_or_create(
            user=user, contactmoment_url=question_ok2.url
        )
        answer_text = question_ok2.answer.answer if question_ok2.answer else None

        return QuestionValidator.validate_python(
            {
                "identification": question_ok2.nummer,
                "api_source_url": question_ok2.url,
                "api_source_uuid": str(question_ok2.question_kcm_uuid),
                "subject": question_ok2.onderwerp,
                "question_text": question_ok2.question,
                "answer_text": answer_text,
                "registered_date": question_ok2.plaatsgevonden_op,
                "status": "Beantwoord" if answer_text is not None else "Onbeantwoord",
                "channel": question_ok2.kanaal,
                "case_detail_url": getattr(question_ok2, "zaak_url", None),
                "new_answer_available": self._has_new_answer_available(
                    question_ok2, answer=answer_metadata
                ),
                "api_service": KlantenServiceType.OPENKLANT2,
            }
        )

    def _has_new_answer_available(
        self, question: OpenKlant2Question, answer: KlantContactMomentAnswer
    ) -> bool:
        answer_is_recent = instance_is_new(
            question.answer,
            "plaatsgevonden_op",
            timedelta(days=settings.CONTACTMOMENT_NEW_DAYS),
        )
        return answer_is_recent and not answer.is_seen

    def list_questions_for_zaak(
        self,
        zaak: Zaak,
        user: User,
    ) -> list[Question]:
        params: ListKlantContactParams = {
            "onderwerpobject__onderwerpobjectidentificatorObjectId": zaak.identificatie,
            "expand": ["hadBetrokkenen"],
        }
        klantcontacten_for_zaak = self.client.klant_contact.list_iter(params=params)
        if not (partij := self.get_partij_for_user(user)):
            logger.error("Partij not found where one was expected", user=user)
            return []

        def partij_is_initiator(klantcontact: KlantContact) -> bool:
            if _expand := klantcontact.get("_expand"):
                if had_betrokkenen := _expand.get("hadBetrokkenen"):
                    for betrokkene in had_betrokkenen:
                        was_partij = betrokkene.get("wasPartij")
                        if was_partij is None:
                            continue
                        partij_was_betrokkene = was_partij["uuid"] == partij["uuid"]
                        partij_was_initiator = betrokkene["initiator"]

                        if partij_was_betrokkene and partij_was_initiator:
                            return True

            return False

        # only show questions initiated by the current user
        klantcontacten_for_initiator = filter(
            partij_is_initiator,
            klantcontacten_for_zaak,
        )

        questions = [
            OpenKlant2Question.from_klantcontact_and_answer(klantcontact, None)
            for klantcontact in klantcontacten_for_initiator
        ]
        return self._build_question_dtos(questions_ok2=questions, user=user)
