import datetime
import logging
import uuid
from datetime import timedelta
from typing import Iterable, Literal, NotRequired, Protocol, Self

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import glom
from ape_pie.client import APIClient
from attr import dataclass
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
from open_inwoner.kvk.branches import get_kvk_branch_number
from open_inwoner.openklant.api_models import (
    ContactMoment,
    ContactMomentCreateData,
    Klant,
    KlantContactMoment,
    KlantContactRol,
    KlantCreateData,
    ObjectContactMoment,
)
from open_inwoner.openklant.constants import KlantenServiceType, Status
from open_inwoner.openklant.models import (
    ContactFormSubject,
    KlantContactMomentAnswer,
    OpenKlant2Config,
    OpenKlantConfig,
)
from open_inwoner.openklant.wrap import (
    contactmoment_has_new_answer,
    fetch_klantcontactmoment,
    fetch_klantcontactmomenten,
    get_kcm_answer_mapping,
)
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.clients import MultiZgwClientProxy
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.utils.api import ClientError, get_json_response
from open_inwoner.utils.logentry import system_action
from open_inwoner.utils.time import instance_is_new
from openklant2.client import OpenKlant2Client
from openklant2.types.resources.digitaal_adres import DigitaalAdres
from openklant2.types.resources.klant_contact import (
    KlantContact,
    ListKlantContactParams,
)
from openklant2.types.resources.partij import Partij, PartijListParams

logger = logging.getLogger(__name__)


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
    source_url: str  # points to contactmoment or klantcontact
    subject: str
    registered_date: datetime.datetime
    question_text: str
    answer_text: str | None
    status: str
    channel: str
    case_detail_url: str | None = None

    api_service: KlantenServiceType
    new_answer_available: bool = False


QuestionValidator = TypeAdapter(Question)


class KlantenService(Protocol):
    config: OpenKlantConfig | OpenKlant2Config
    service_config: ServiceConfig
    client: APIClient

    def get_fetch_parameters(
        self,
        request=None,
        user: User | None = None,
        use_vestigingsnummer: bool = False,
    ) -> FetchParameters | None:
        """
        Determine the parameters used to perform Klanten/Contactmomenten fetches
        """
        user = user or request.user

        if user.bsn:
            return {"user_bsn": user.bsn}
        elif user.kvk:
            kvk_or_rsin = user.kvk
            config = OpenKlantConfig.get_solo()
            if config.use_rsin_for_innNnpId_query_parameter:
                kvk_or_rsin = user.rsin

            if use_vestigingsnummer:
                vestigingsnummer = get_kvk_branch_number(request.session)
                if vestigingsnummer:
                    return {
                        "user_kvk_or_rsin": kvk_or_rsin,
                        "vestigingsnummer": vestigingsnummer,
                    }

            return {"user_kvk_or_rsin": kvk_or_rsin}

        return None


class eSuiteKlantenService(KlantenService):
    config: OpenKlantConfig

    def __init__(self, config: OpenKlantConfig | None = None):
        self.config = config or OpenKlantConfig.get_solo()
        if not self.config:
            raise RuntimeError("eSuiteKlantenService instance needs a configuration")

        self.service_config = self.config.klanten_service
        if not self.service_config:
            raise RuntimeError(
                "eSuiteKlantenService instance needs a servivce configuration"
            )

        self.client = build_zgw_client(service=self.service_config)
        if not self.client:
            raise RuntimeError("eSuiteKlantenService instance needs a client")

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
    ):
        klanten = None
        # this is technically a search operation and could return multiple records
        if user_bsn:
            klanten = self._retrieve_klanten_for_bsn(user_bsn)
        elif user_kvk_or_rsin:
            klanten = self._retrieve_klanten_for_kvk_or_rsin(user_kvk_or_rsin)

        return klanten[0] if klanten else None

    def _retrieve_klanten_for_bsn(self, user_bsn: str) -> list[Klant]:
        try:
            response = self.client.get(
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

    def _retrieve_klanten_for_kvk_or_rsin(
        self, user_kvk_or_rsin: str, *, vestigingsnummer=None
    ) -> list[Klant]:
        params = {"subjectNietNatuurlijkPersoon__innNnpId": user_kvk_or_rsin}

        if vestigingsnummer:
            params = {
                "subjectVestiging__vestigingsNummer": vestigingsnummer,
            }

        try:
            response = self.client.get(
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
            response = self.client.post("klanten", json=payload)
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
            response = self.client.post(
                "klanten",
                json=payload,
            )
            data = get_json_response(response)
        except (RequestException, ClientError):
            logger.exception("exception while making request")
            return None

        klant = factory(Klant, data)

        return klant

    def update_user_from_klant(self, klant: Klant, user: User):
        update_data = {}

        if klant.telefoonnummer and klant.telefoonnummer != user.phonenumber:
            update_data["phonenumber"] = klant.telefoonnummer

        if klant.emailadres and klant.emailadres != user.email:
            if not User.objects.filter(email__iexact=klant.emailadres).exists():
                update_data["email"] = klant.emailadres

        config = SiteConfiguration.get_solo()
        if config.enable_notification_channel_choice:
            if (
                klant.toestemming_zaak_notificaties_alleen_digitaal is True
                and user.case_notification_channel
                != NotificationChannelChoice.digital_only
            ):
                update_data[
                    "case_notification_channel"
                ] = NotificationChannelChoice.digital_only

            elif (
                klant.toestemming_zaak_notificaties_alleen_digitaal is False
                and user.case_notification_channel
                != NotificationChannelChoice.digital_and_post
            ):
                update_data[
                    "case_notification_channel"
                ] = NotificationChannelChoice.digital_and_post
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
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        klant = factory(Klant, data)

        return klant


class eSuiteVragenService(KlantenService):
    config: OpenKlantConfig

    def __init__(self, config: OpenKlantConfig | None = None):
        self.config = config or OpenKlantConfig.get_solo()
        if not self.config:
            raise RuntimeError("eSuiteVragenService instance needs a configuration")

        self.service_config = self.config.contactmomenten_service
        if not self.service_config:
            raise RuntimeError(
                "eSuiteVragenService instance needs a servivce configuration"
            )

        self.client = build_zgw_client(service=self.service_config)
        if not self.client:
            raise RuntimeError("eSuiteVragenService instance needs a client")

    #
    # contactmomenten
    #
    def retrieve_contactmoment(self, url) -> ContactMoment | None:
        try:
            response = self.client.get(url)
            data = get_json_response(response)
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
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
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
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
                        "rol": rol,
                    },
                )
            except (RequestException, ClientError) as e:
                logger.exception("exception while making request", exc_info=e)
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
        except (RequestException, ClientError) as exc:
            logger.exception("exception while making request", exc_info=exc)
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
            response = self.client.get(
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
            response = self.client.get(
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
        e_suite_subject_code = getattr(kcm.contactmoment, "onderwerp", "")

        try:
            subject = ContactFormSubject.objects.get(subject_code=e_suite_subject_code)
        except ContactFormSubject.MultipleObjectsReturned as exc:
            logger.warning(
                "Multiple OIP subjects mapped to the same e-suite subject code for ",
                "contactmoment %s; using the first one",
                kcm.contactmoment.url,
                exc_info=exc,
            )
            return ContactFormSubject.objects.first().subject
        except ContactFormSubject.DoesNotExist as exc:
            logger.warning(
                "Could not determine OIP subject for contactmoment %s; "
                "falling back on e-suite subject code ('onderwerp')",
                kcm.contactmoment.url,
                exc_info=exc,
            )
            return e_suite_subject_code

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

    def _get_question_data(
        self,
        kcm: KlantContactMoment,
        local_kcm_mapping: dict[str, KlantContactMomentAnswer] | None = None,
    ) -> Question:

        if isinstance(kcm.contactmoment, str):
            raise ValueError("Received unresolved contactmoment")

        question_data = {
            "answer_text": kcm.contactmoment.antwoord,
            "identification": kcm.contactmoment.identificatie,
            "question_text": kcm.contactmoment.tekst,
            "new_answer_available": self.contactmoment_has_new_answer(
                kcm.contactmoment, local_kcm_mapping=local_kcm_mapping
            ),
            "subject": self._get_kcm_subject(kcm) or "",
            "registered_date": kcm.contactmoment.registratiedatum,
            "status": str(Status.safe_label(kcm.contactmoment.status, _("Onbekend"))),
            "case_detail_url": reverse(
                "cases:contactmoment_detail", kwargs={"kcm_uuid": kcm.uuid}
            ),
            "channel": kcm.contactmoment.kanaal.title(),
            "source_url": kcm.contactmoment.url,
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

        klant_config = OpenKlantConfig.get_solo()
        if exclude_range := klant_config.exclude_contactmoment_kanalen:
            kcms = [
                item
                for item in kcms
                if glom.glom(item, "contactmoment.kanaal") not in exclude_range
            ]

        contactmomenten = [
            self._get_question_data(
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

        local_kcm, is_created = KlantContactMomentAnswer.objects.get_or_create(  # noqa
            user=user, contactmoment_url=kcm.contactmoment.url
        )
        if not local_kcm.is_seen:
            local_kcm.is_seen = True
            local_kcm.save()

        zaak_with_api_group = None

        ocm = self.retrieve_objectcontactmoment(kcm.contactmoment, "zaak")
        if ocm and ocm.object_type == "zaak":
            zaak_url = ocm.object
            groups = list(ZGWApiGroupConfig.objects.all())
            proxy = MultiZgwClientProxy([group.zaken_client for group in groups])
            proxy_response = proxy.fetch_case_by_url_no_cache(zaak_url)
            cases_found = proxy_response.truthy_responses
            if (case_count := len(cases_found)) == 0:
                logger.error(
                    "Unable to find matched contactmomenten zaak in any zgw backend"
                )
            else:
                zaak, client = cases_found[0].result, cases_found[0].client
                group = ZGWApiGroupConfig.objects.resolve_group_from_hints(
                    client=client
                )
                zaak_with_api_group = ZaakWithApiGroup(zaak=zaak, api_group=group)
                if case_count > 1:
                    # In principle this should not happen, a zaak should be stored in
                    # exactly one backend. But: https://www.xkcd.com/2200/
                    # We should at least receive a ping if this happens.
                    logger.error("Found one zaak in multiple backends")

        return self._get_question_data(kcm), zaak_with_api_group


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


class OpenKlant2Service(KlantenService):
    config: OpenKlant2Config
    client: OpenKlant2Client

    def __init__(self, config: OpenKlant2Config | None = None):
        self.config = config or OpenKlant2Config.from_django_settings()
        if not self.config:
            raise RuntimeError("OpenKlant2Service instance needs a configuration")

        self.client = OpenKlant2Client(
            base_url=self.config.api_url,
            request_kwargs={
                "headers": {"Authorization": f"Token {self.config.api_token}"}
            },
        )
        if not self.client:
            raise RuntimeError("OpenKlant2Service instance needs a client")

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
            "partijIdentificator__codeObjecttype": "inp",
            "partijIdentificator__objectId": bsn,
            "soortPartij": "persoon",
        }

    @staticmethod
    def _kvk_list_param(kvk: str) -> PartijListParams:
        return {
            "partijIdentificator__codeSoortObjectId": "kvk",
            "partijIdentificator__codeRegister": "hr",
            "partijIdentificator__codeObjecttype": "nnp",
            "partijIdentificator__objectId": kvk,
            "soortPartij": "organisatie",
        }

    @staticmethod
    def _vestigingsnummer_list_param(vestigingsnummer: str) -> PartijListParams:
        return {
            "partijIdentificator__codeSoortObjectId": "vtn",
            "partijIdentificator__codeRegister": "hr",
            "partijIdentificator__codeObjecttype": "nnp",
            "partijIdentificator__objectId": vestigingsnummer,
            "soortPartij": "organisatie",
        }

    def find_persoon_for_bsn(self, bsn: str) -> Partij | None:
        return self.find_partij_for_params(params=self._bsn_list_param(bsn))

    def find_organisatie_for_kvk(self, kvk: str) -> Partij | None:
        return self.find_partij_for_params(params=self._kvk_list_param(kvk))

    def find_organisatie_for_vestigingsnummer(
        self, vestigingsnummer: str
    ) -> Partij | None:
        return self.find_partij_for_params(
            params=self._vestigingsnummer_list_param(vestigingsnummer)
        )

    def get_or_create_partij_for_user(
        self, fetch_params: FetchParameters, user: User
    ) -> tuple[Partij | None, bool]:
        partij = None
        created = False

        if bsn := fetch_params.get("user_bsn"):
            if not (persoon := self.find_persoon_for_bsn(bsn)):
                persoon = self.client.partij.create_persoon(
                    data={
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
                )
                created = True

                try:
                    self.client.partij_identificator.create(
                        data={
                            "identificeerdePartij": {"uuid": persoon["uuid"]},
                            "partijIdentificator": {
                                "codeObjecttype": "inp",
                                "codeSoortObjectId": "bsn",
                                "objectId": bsn,
                                "codeRegister": "brp",
                            },
                        }
                    )
                except Exception:
                    logger.exception("Unable to register identificatoren for partij")

            partij = persoon

        elif kvk := fetch_params.get("user_kvk_or_rsin"):

            # Prefer vestigingsnummer if present, to stay consistent with OK1 behavior
            organisatie: Partij | None
            if vestigingsnummer := fetch_params.get("vestigingsnummer"):
                organisatie = self.find_organisatie_for_vestigingsnummer(
                    vestigingsnummer
                )
            else:
                organisatie = self.find_organisatie_for_kvk(kvk)

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

                for soort_object_id, object_id in (
                    ("kvk", kvk),
                    ("vtn", vestigingsnummer),
                ):
                    if object_id:
                        try:
                            self.client.partij_identificator.create(
                                data={
                                    "identificeerdePartij": {
                                        "uuid": organisatie["uuid"]
                                    },
                                    "partijIdentificator": {
                                        "codeObjecttype": "nnp",
                                        "codeSoortObjectId": soort_object_id,
                                        "objectId": object_id,
                                        "codeRegister": "hr",
                                    },
                                }
                            )
                        except Exception:
                            logger.exception(
                                "Unable to register identificatoren for partij"
                            )

            partij = organisatie

        if not partij:
            logger.error("Unable to create OpenKlant2 partij for user")
            return None, False

        msg = (
            f"{'created' if created else 'retrieved'} partij {partij['uuid']} for user"
        )
        system_action(msg, content_object=user)

        return partij, created

    def retrieve_digitale_addressen_for_partij(
        self, partij_uuid: str
    ) -> list[DigitaalAdres]:
        expand_partij = self.client.partij.retrieve(
            partij_uuid, params={"expand": ["digitaleAdressen"]}
        )

        if expand := expand_partij.get("_expand"):
            if digitale_adressen := expand.get("digitaleAdressen"):
                return digitale_adressen

        # TODO: A missing _expand can mean there are no addresses.
        # See: https://github.com/maykinmedia/open-klant/issues/243
        return []

    def filter_digitale_addressen_for_partij(
        self,
        partij_uuid: str,
        *,
        soortDigitaalAdres: str,
        adressen: Iterable[DigitaalAdres] | None = None,
    ) -> list[DigitaalAdres]:
        if adressen is None:
            adressen = self.retrieve_digitale_addressen_for_partij(partij_uuid)

        return [
            digitaal_adres
            for digitaal_adres in adressen
            if digitaal_adres["soortDigitaalAdres"] == soortDigitaalAdres
        ]

    def get_or_create_digitaal_adres(
        self,
        partij_uuid: str,
        soortAdres: Literal["email", "telefoon"],
        adres: str,
    ) -> tuple[DigitaalAdres, bool]:
        digitale_adressen = self.filter_digitale_addressen_for_partij(
            partij_uuid, soortDigitaalAdres=soortAdres
        )
        for digitaal_adres in digitale_adressen:
            if digitaal_adres["adres"] == adres:
                return digitaal_adres, False

        return (
            self.client.digitaal_adres.create(
                data={
                    "adres": adres,
                    "soortDigitaalAdres": soortAdres,
                    "verstrektDoorPartij": {
                        "uuid": partij_uuid,
                    },
                    "verstrektDoorBetrokkene": None,
                    "omschrijving": "OIP profiel",
                }
            ),
            True,
        )

    def update_user_from_partij(self, partij_uuid: str, user: User):
        update_data = {}

        adressen = self.retrieve_digitale_addressen_for_partij(partij_uuid)

        if email_adressen := self.filter_digitale_addressen_for_partij(
            partij_uuid, soortDigitaalAdres="email", adressen=adressen
        ):
            email = email_adressen[0]["adres"]
            if not User.objects.filter(email__iexact=email).exists():
                update_data["email"] = email

        if phone_adressen := self.filter_digitale_addressen_for_partij(
            partij_uuid, soortDigitaalAdres="telefoon", adressen=adressen
        ):
            update_data["phonenumber"] = phone_adressen[0]["adres"]

        if update_data:
            for attr, value in update_data.items():
                setattr(user, attr, value)
            user.save(update_fields=update_data.keys())

            system_action(
                f"updated user from klant API with fields: {', '.join(sorted(update_data.keys()))}",
                content_object=user,
            )

    def update_partij_from_user(self, partij_uuid: str, user: User):
        updated_fields = []
        for attr, soort_adres in (("email", "email"), ("phonenumber", "telefoon")):
            _, created = self.get_or_create_digitaal_adres(
                partij_uuid,
                soort_adres,
                getattr(user, attr),
            )
            if created:
                updated_fields.append(f"digitaleAddresen.{soort_adres}")

        if updated_fields:
            system_action(
                f"updated Partij from user with fields: {', '.join(sorted(updated_fields))}",
                content_object=user,
            )

    def create_question(
        self, partij_uuid: str, question: str, subject: str
    ) -> OpenKlant2Question:

        if len(question.rstrip()) == 0:
            raise ValueError("You must provide a question")

        if self.mijn_vragen_actor is None:
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
        logger.info("Created klantcontact: %s", klantcontact["uuid"])

        betrokkene = self.client.betrokkene.create(
            data={
                "rol": "klant",
                "hadKlantcontact": {"uuid": klantcontact["uuid"]},
                "initiator": True,
                "wasPartij": {"uuid": partij_uuid},
                "organisatienaam": "Open Inwoner Platform",
            }
        )
        logger.info("Created betrokkene: %s", betrokkene["uuid"])

        taak = self.client.interne_taak.create(
            data={
                "aanleidinggevendKlantcontact": {"uuid": klantcontact["uuid"]},
                "toelichting": "Beantwoorden vraag",
                "gevraagdeHandeling": "Vraag beantwoorden in aanleiding gevend klant contact",
                "status": "te_verwerken",
                "toegewezenAanActor": {"uuid": str(self.mijn_vragen_actor)},
            }
        )
        logger.info("Created taak: %s", taak["uuid"])

        return OpenKlant2Question.from_klantcontact_and_answer(klantcontact)

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
                ("_expand.hadBetrokkenen", ["wasPartij.uuid"]),
            ),
            klantcontacten,
        )

        return klantcontacten_for_partij

    def questions_for_partij(self, partij_uuid: str) -> list[OpenKlant2Question]:
        answers_for_klantcontact_uuid = {}
        question_uuids = []
        klantcontact_uuid_to_klantcontact_object = {}

        for klantcontact in self.klantcontacten_for_partij(
            partij_uuid, kanaal=self.config.mijn_vragen_kanaal
        ):
            klantcontact_uuid_to_klantcontact_object[
                klantcontact["uuid"]
            ] = klantcontact

            # A klantcontact is an answer if it is linked to a Question via an onderwerp object
            if onderwerp_objecten := klantcontact["gingOverOnderwerpobjecten"]:

                # To which question klantcontact is this an answer?
                answer_onderwerp_object = self.client.onderwerp_object.retrieve(
                    onderwerp_objecten[0]["uuid"]
                )

                if not answer_onderwerp_object["wasKlantcontact"]:
                    logger.error(
                        "Onderwerp object %s should point to question klantcontact",
                        answer_onderwerp_object["uuid"],
                    )
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
        if bsn := fetch_params.get("user_bsn"):
            partij = self.find_persoon_for_bsn(bsn)
        elif kvk_or_rsin := fetch_params.get("user_kvk_or_rsin"):
            partij = self.find_organisatie_for_kvk(kvk_or_rsin)

        questions = self.questions_for_partij(partij_uuid=partij["uuid"])
        return self._reformat_questions(questions, user)

    # TODO: handle `status` + `new_answer_available`
    # `case_detail_url`: will be handled in integration of detail view
    # `status`: eSuite has three: "nieuw", "in behandeling", "afgehandeld"
    def _reformat_questions(
        self,
        questions_ok2: list[OpenKlant2Question],
        user: User,
    ) -> list[Question]:
        questions = []
        for q in questions_ok2:
            answer_metadata, _ = KlantContactMomentAnswer.objects.get_or_create(
                user=user, contactmoment_url=q.url
            )
            question = {
                "identification": q.nummer,
                "source_url": q.url,
                "subject": q.onderwerp,
                "registered_date": q.plaatsgevonden_op,
                "question_text": q.question,
                "answer_text": getattr(q.answer, "answer", None),
                "status": "",
                "channel": q.kanaal,
                "case_detail_url": "",
                "api_service": KlantenServiceType.OPENKLANT2,
                "new_answer_available": self._has_new_answer_available(
                    q, answer=answer_metadata
                ),
            }
            questions.append(question)
        return [QuestionValidator.validate_python(q) for q in questions]

    def _has_new_answer_available(
        self, question: OpenKlant2Question, answer: KlantContactMomentAnswer
    ) -> bool:
        answer_is_recent = instance_is_new(
            question.answer,
            "plaatsgevonden_op",
            timedelta(days=settings.CONTACTMOMENT_NEW_DAYS),
        )
        return answer_is_recent and not answer.is_seen
