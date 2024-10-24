import datetime
import logging
import uuid
from typing import Iterable, Literal, Self

from django.utils import timezone

import glom
from attr import dataclass

from open_inwoner.accounts.choices import NotificationChannelChoice
from open_inwoner.accounts.models import User
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.api_models import Klant
from open_inwoner.openklant.clients import build_klanten_client
from open_inwoner.openklant.models import OpenKlant2Config
from open_inwoner.utils.logentry import system_action
from openklant2.client import OpenKlant2Client
from openklant2.types.resources.digitaal_adres import DigitaalAdres
from openklant2.types.resources.klant_contact import (
    KlantContact,
    ListKlantContactParams,
)
from openklant2.types.resources.partij import Partij, PartijListParams

from .wrap import FetchParameters, get_fetch_parameters

logger = logging.getLogger(__name__)


def get_or_create_klant_from_request(request):
    if not (client := build_klanten_client()):
        return

    if (fetch_params := get_fetch_parameters(request)) is None:
        return

    if klant := client.retrieve_klant(**fetch_params):
        msg = "retrieved klant for user"
    elif klant := client.create_klant(**fetch_params):
        msg = f"created klant ({klant.klantnummer}) for user"
    else:
        return

    system_action(msg, content_object=request.user)
    return klant


def update_user_from_klant(klant: Klant, user: User):
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
            and user.case_notification_channel != NotificationChannelChoice.digital_only
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


@dataclass(frozen=True)
class OpenKlant2Answer:
    answer: str
    answer_kcm_uuid: str
    nummer: str
    plaatsgevonden_op: datetime.datetime

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
class OpenKlant2Question:
    question: str
    question_kcm_uuid: str
    nummer: str
    plaatsgevonden_op: datetime.datetime

    answer: OpenKlant2Answer | None = None

    @classmethod
    def from_klantcontact_and_answer(
        cls, klantcontact: KlantContact, answer: OpenKlant2Answer | None = None
    ) -> Self:
        if klantcontact["inhoud"] is None:
            raise ValueError("Klantcontact did not contain any content in `inhoud`")

        return cls(
            question=klantcontact["inhoud"],
            question_kcm_uuid=klantcontact["uuid"],
            nummer=klantcontact["nummer"],
            plaatsgevonden_op=datetime.datetime.fromisoformat(
                klantcontact["plaatsgevondenOp"]
            ),
            answer=answer,
        )


class OpenKlant2Service:
    config: OpenKlant2Config
    client: OpenKlant2Client

    def __init__(self, config: OpenKlant2Config | None = None):
        self.config = config or OpenKlant2Config.from_django_settings()
        self.client = OpenKlant2Client(
            api_url=self.config.api_url,
            api_token=self.config.api_token,
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
    ) -> Partij | None:
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
            return

        msg = (
            f"{'created' if created else 'retrieved'} partij {partij['uuid']} for user"
        )
        system_action(msg, content_object=user)

        return partij

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
        params: ListKlantContactParams = {
            "expand": [
                "leiddeTotInterneTaken",
                "gingOverOnderwerpobjecten",
                "hadBetrokkenen",
                "hadBetrokkenen.wasPartij",
            ],
        }
        if kanaal:
            params["kanaal"] = kanaal

        klantcontacten = self.client.klant_contact.list_iter(params=params)

        # There is currently no good way to filter the klantcontacten by a
        # Partij (see https://github.com/maykinmedia/open-klant/issues/256). So
        # unfortunately, we have to fetch all rows and do the filtering client
        # side.
        klantcontacten = self.client.klant_contact.list_iter(
            params={
                "expand": [
                    "leiddeTotInterneTaken",
                    "gingOverOnderwerpobjecten",
                    "hadBetrokkenen",
                    "hadBetrokkenen.wasPartij",
                ],
                "kanaal": self.config.mijn_vragen_kanaal,
            }
        )

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
