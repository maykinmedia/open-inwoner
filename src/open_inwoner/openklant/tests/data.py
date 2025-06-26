from requests.exceptions import RequestException
from zgw_consumers.constants import APITypes

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
)
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import ESuiteKlantConfig
from open_inwoner.openzaak.tests.factories import (
    ServiceFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import ZAKEN_ROOT
from open_inwoner.utils.test import paginated_response

KLANTEN_ROOT = "https://klanten.nl/api/v1/"
OPENKLANT2_ROOT = "http://localhost:8338/klantinteracties/api/v1"
CONTACTMOMENTEN_ROOT = "https://contactmomenten.nl/api/v1/"


class MockAPIData:
    @classmethod
    def setUpServices(cls):
        config = ESuiteKlantConfig.get_solo()
        config.klanten_service = ServiceFactory(
            api_root=KLANTEN_ROOT, api_type=APITypes.kc
        )
        config.contactmomenten_service = ServiceFactory(
            api_root=CONTACTMOMENTEN_ROOT, api_type=APITypes.cmc
        )
        config.save()

        # services
        ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
        )


class MockAPIReadPatchData(MockAPIData):
    def __init__(self, eherkenning_kvk: str | None = None):
        # allow specification of KVK number for mocks because KVK must be unique
        self.eherkenning_kvk = eherkenning_kvk or "12345678"

        self.user = DigidUserFactory(
            email="old@example.com",
            phonenumber="0100000000",
        )
        self.user_without_klant = DigidUserFactory(
            email="new@example.com",
            phonenumber="0100000000",
            bsn="665155311",
        )
        self.eherkenning_user = eHerkenningUserFactory(
            email="old2@example.com",
            kvk=self.eherkenning_kvk,
            rsin="000000000",
        )
        self.klant_bsn_old = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="bad@example.com",
            telefoonnummer="",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.klant_bsn_updated = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="good@example.com",
            telefoonnummer="0123456789",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.created_klant_bsn = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="87654321",
            subjectIdentificatie={
                "inpBsn": "665155311",
            },
            url=f"{KLANTEN_ROOT}klant/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            emailadres="foooo@bar.com",
            telefoonnummer="0199995544",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.created_klant_bsn_updated = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="87654321",
            subjectIdentificatie={
                "inpBsn": "665155311",
            },
            url=f"{KLANTEN_ROOT}klant/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            emailadres="foooo@bar.com",
            telefoonnummer="0199995544",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.klant_eherkenning_old = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            subjectIdentificatie={
                "innNnpId": "87654321",
            },
            emailadres="bad@example.com",
            telefoonnummer="",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.klant_eherkenning_updated = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            subjectIdentificatie={
                "innNnpId": "87654321",
            },
            emailadres="good@example.com",
            telefoonnummer="0123456789",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )

    def install_mocks(self, m) -> "MockAPIReadPatchData":
        self.matchers = [
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
                json=paginated_response([self.klant_bsn_old]),
            ),
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant_bsn_updated,
                status_code=200,
            ),
            # Create and update flow
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user_without_klant.bsn}",
                json=paginated_response([]),
            ),
            m.post(
                f"{KLANTEN_ROOT}klanten",
                json=self.created_klant_bsn,
                status_code=201,
            ),
            m.patch(
                f"{KLANTEN_ROOT}klant/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                json=self.created_klant_bsn_updated,
                status_code=200,
            ),
        ]
        return self

    def install_mocks_eherkenning(self, m, use_rsin=True) -> "MockAPIReadPatchData":
        if use_rsin:
            first_eherkenning_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.rsin}",
                json=paginated_response([self.klant_eherkenning_old]),
            )
        else:
            first_eherkenning_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
                json=paginated_response([self.klant_eherkenning_old]),
            )
        self.matchers = [
            first_eherkenning_matcher,
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant_eherkenning_updated,
                status_code=200,
            ),
        ]
        return self


class MockAPIReadData(MockAPIData):
    def __init__(self, eherkenning_kvk: str | None = None):
        # allow specification of KVK number for mocks because KVK must be unique
        self.eherkenning_kvk = eherkenning_kvk or "12345678"

        self.user = DigidUserFactory(
            bsn="100000001",
        )
        self.eherkenning_user = eHerkenningUserFactory(
            kvk=self.eherkenning_kvk,
            rsin="000000000",
        )
        self.eherkenning_user_vestiging = eHerkenningVestigingUserFactory(
            kvk=self.eherkenning_kvk,
            rsin="000000000",
            vestiging="1234",
        )

        self.klant_bsn = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="foo@example.com",
            telefoonnummer="0612345678",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
            voornaam="John",
            achternaam="Doe",
            voorvoegselAchternaam="van der",
            bedrijfsnaam="",
        )
        self.klant_kvk = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="87654321",
            subjectIdentificatie={
                "innNnpId": "87654321",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            emailadres="foo@bar.com",
            telefoonnummer="0687654321",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
            voornaam="",
            achternaam="",
            voorvoegselAchternaam="",
            bedrijfsnaam="AcmeCorp B.V.",
        )
        self.klant_vestiging = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="11111111",
            subjectIdentificatie={
                "vestigingsNummer": "123456789000",
            },
            url=f"{KLANTEN_ROOT}klant/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            emailadres="foo@bar.com",
            telefoonnummer="0612345678",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
            voornaam="",
            achternaam="",
            voorvoegselAchternaam="",
            bedrijfsnaam="AcmeCorp B.V.",
        )
        self.contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            bronorganisatie="123456789",
            identificatie="AB123",
            type="SomeType",
            kanaal="Mail",
            registratiedatum="2022-01-01T12:00:00Z",
            status=Status.afgehandeld.value,
            tekst="Garage verbouwen?",
            antwoord="foo",
            onderwerp="e_suite_subject_code",
        )
        self.contactmoment2 = generate_oas_component_cached(
            "cmc",
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd",
            bronorganisatie="123456789",
            identificatie="AB123",
            type="SomeType",
            kanaal="Mail",
            registratiedatum="2023-01-01T12:00:00Z",
            status=Status.afgehandeld.value,
            tekst="Garage verbouwen?",
            antwoord="bar",
            onderwerp="e_suite_subject_code",
        )
        self.contactmoment_vestiging = generate_oas_component_cached(
            "cmc",
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee",
            bronorganisatie="123456789",
            identificatie="AB123",
            type="SomeType",
            kanaal="Mail",
            registratiedatum="2022-01-01T12:00:00Z",
            status=Status.afgehandeld.value,
            tekst="Garage verbouwen?",
            antwoord="baz",
            onderwerp="e_suite_subject_code",
        )
        self.contactmoment_intern = generate_oas_component_cached(
            "cmc",
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/bbbbbbbb-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            bronorganisatie="123456789",
            identificatie="AB123",
            type="SomeType",
            kanaal="intern_initiatief",
            registratiedatum="2022-01-01T12:00:00Z",
            status=Status.afgehandeld.value,
            tekst="Garage verbouwen?",
            antwoord="foo",
            onderwerp="e_suite_subject_code",
        )
        self.klant_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant_bsn["url"],
            contactmoment=self.contactmoment["url"],
            rol="gesprekspartner",
        )
        self.klant_contactmoment2 = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee",
            klant=self.klant_kvk["url"],
            contactmoment=self.contactmoment2["url"],
            rol="gesprekspartner",
        )
        self.klant_contactmoment3 = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd",
            klant=self.klant_bsn["url"],
            contactmoment=self.contactmoment_vestiging["url"],
            rol="gesprekspartner",
        )
        self.klant_contactmoment4 = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            klant=self.klant_vestiging["url"],
            contactmoment=self.contactmoment_vestiging["url"],
            rol="gesprekspartner",
        )
        self.klant_contactmoment_vestiging = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            klant=self.klant_vestiging["url"],
            contactmoment=self.contactmoment_vestiging["url"],
            rol="gesprekspartner",
        )
        self.klant_contactmoment_intern = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            uuid="bbbbbbbb-aaaa-aaaa-aaaa-cccccccccccc",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/bbbbbbbb-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant_bsn["url"],
            contactmoment=self.contactmoment_intern["url"],
            rol="gesprekspartner",
        )
        self.objectcontactmoment_other = generate_oas_component_cached(
            "cmc",
            "schemas/Objectcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten/bb51784c-fa2c-4f65-b24e-7179b615efac",
            object="http://documenten.nl/api/v1/1",
            contactmoment=self.contactmoment["url"],
        )
        # Force objectType other than zaak, to verify that filtering works
        self.objectcontactmoment_other["objectType"] = "document"
        self.objectcontactmoment_zaak = generate_oas_component_cached(
            "cmc",
            "schemas/Objectcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten/77880671-b88a-44ed-ba24-dc2ae688c2ec",
            object=f"{ZAKEN_ROOT}zaken/410bb717-ff3d-4fd8-8357-801e5daf9775",
            objectType="zaak",
            contactmoment=self.contactmoment["url"],
        )
        self.zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="410bb717-ff3d-4fd8-8357-801e5daf9775",
            url=f"{ZAKEN_ROOT}zaken/410bb717-ff3d-4fd8-8357-801e5daf9775",
            identificatie="053ESUITE5422021",
        )

    def install_mocks(self, m, link_objectcontactmomenten=False) -> "MockAPIReadData":
        for resource_attr in [
            "klant_bsn",
            "klant_kvk",
            "klant_vestiging",
            "contactmoment",
            "contactmoment2",
            "contactmoment_vestiging",
            "contactmoment_intern",
            "klant_contactmoment",
            "klant_contactmoment2",
            "klant_contactmoment3",
            "klant_contactmoment4",
            "klant_contactmoment_vestiging",
            "zaak",
        ]:
            resource = getattr(self, resource_attr)
            m.get(resource["url"], json=resource)

        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
            json=paginated_response([self.klant_bsn]),
        )

        # Mock both RSIN and KvK fetch variations, can be toggled with feature flag
        # `use_rsin_for_innNnpId_query_parameter`
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
            json=paginated_response([self.klant_kvk]),
        )
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.rsin}",
            json=paginated_response([self.klant_kvk]),
        )
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectVestiging__vestigingsNummer=1234",
            json=paginated_response([self.klant_vestiging]),
        )

        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant_bsn['url']}",
            json=paginated_response(
                [self.klant_contactmoment, self.klant_contactmoment_intern]
            ),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant_kvk['url']}",
            json=paginated_response([self.klant_contactmoment2]),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant_vestiging['url']}",
            json=paginated_response([self.klant_contactmoment4]),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant_contactmoment_intern['url']}",
            json=paginated_response([self.klant_contactmoment_intern]),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten?contactmoment={self.contactmoment['url']}",
            json=paginated_response(
                [self.objectcontactmoment_other, self.objectcontactmoment_zaak]
                if link_objectcontactmomenten
                else []
            ),
        )
        # If exceptions occur while fetching objectcontactmomenten, the contactmoment
        # should still show
        m.get(
            f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten?contactmoment={self.contactmoment2['url']}",
            exc=RequestException,
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten?contactmoment={self.contactmoment_vestiging['url']}",
            exc=RequestException,
        )

        return self


class MockAPICreateData(MockAPIData):
    def __init__(self, eherkenning_kvk: str | None = None):
        # allow specification of KVK number for mocks because KVK must be unique
        self.eherkenning_kvk = eherkenning_kvk or "12345678"

        self.user = DigidUserFactory(
            bsn="100000001",
        )
        self.eherkenning_user = eHerkenningUserFactory(
            kvk=self.eherkenning_kvk,
            rsin="000000000",
        )
        self.klant_bsn = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="foo@example.com",
            telefoonnummer="0612345678",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.klant_eherkenning_no_contact_info = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "innNnpId": "87654321",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            voornaam="Foo",
            achternaam="Bar",
            emailadres="",
            telefoonnummer="",
            telefoonnummerAlternatief="",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.klant_bsn_no_contact_info = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            voornaam="Foo",
            achternaam="Bar",
            emailadres="",
            telefoonnummer="",
            telefoonnummerAlternatief="",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )
        self.contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            bronorganisatie="123456789",
            identificatie="AB123",
            type="SomeType",
            kanaal="Mail",
            registratiedatum="2022-01-01T12:00:00Z",
            status=str(Status.nieuw),
            text="hey!\n\nwaddup?",
            antwoord="foo",
            onderwerp="e_suite_subject_code",
        )
        self.klant_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant_bsn["url"],
            contactmoment=self.contactmoment["url"],
            rol="gesprekspartner",
        )

        self.matchers = []

    def install_mocks_anon(self, m) -> "MockAPICreateData":
        self.matchers = [
            m.post(
                f"{CONTACTMOMENTEN_ROOT}contactmomenten",
                json=self.contactmoment,
                status_code=201,
            ),
            m.post(f"{KLANTEN_ROOT}klanten", json=self.klant_bsn, status_code=201),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten",
                json=self.klant_contactmoment,
                status_code=201,
            ),
        ]
        return self

    def install_mocks_anon_without_klant(self, m) -> "MockAPICreateData":
        self.matchers = [
            m.post(f"{KLANTEN_ROOT}klanten", status_code=500),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}contactmomenten",
                json=self.contactmoment,
                status_code=201,
            ),
        ]
        return self

    def install_mocks_digid(self, m) -> "MockAPICreateData":
        self.matchers = [
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
                json=paginated_response([self.klant_bsn]),
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}contactmomenten",
                json=self.contactmoment,
                status_code=201,
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten",
                json=self.klant_contactmoment,
                status_code=201,
            ),
        ]
        return self

    def install_mocks_openklant(self, m):
        self.digid_user = DigidUserFactory()
        m.get(
            "http://localhost:8338/klantinteracties/api/v1/partijen?partijIdentificator__codeSoortObjectId=bsn&partijIdentificator__codeRegister=brp&partijIdentificator__codeObjecttype=natuurlijk_persoon&partijIdentificator__objectId=123456782&soortPartij=persoon",
            headers={"Content-Type": "application/json"},
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "uuid": "7260ea01-12c0-4750-8fd1-dfa777818837",
                    },
                ],
            },
            status_code=200,
        )
        m.get(
            "http://localhost:8338/klantinteracties/api/v1/partijen?partijIdentificator__codeSoortObjectId=bsn&partijIdentificator__codeRegister=brp&partijIdentificator__codeObjecttype=natuurlijk_persoon&partijIdentificator__objectId=100000001&soortPartij=persoon",
            headers={"Content-Type": "application/json"},
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "uuid": "7260ea01-12c0-4750-8fd1-dfa777818837",
                    },
                ],
            },
            status_code=200,
        )

        m.get(
            "http://localhost:8338/klantinteracties/api/v1/partijen/7260ea01-12c0-4750-8fd1-dfa777818837?expand=digitaleAdressen%2Cbetrokkenen%2Cbetrokkenen.hadKlantcontact",
            headers={"Content-Type": "application/json"},
            json={
                "uuid": "7260ea01-12c0-4750-8fd1-dfa777818837",
                "digitaleAdressen": None,
                "voorkeursDigitaalAdres": None,
                "rekeningnummers": None,
                "voorkeursRekeningnummer": None,
                "indicatieGeheimhouding": False,
                "indicatieActief": True,
                "voorkeurstaal": "crp",
                "soortPartij": "persoon",
                "partijIdentificatie": {
                    "contactnaam": {
                        "voorletters": "Dr.",
                        "voornaam": "Test Persoon",
                        "voorvoegselAchternaam": "Mrs.",
                        "achternaam": "Gamble",
                    }
                },
            },
        )
        m.get(
            "http://localhost:8338/klantinteracties/api/v1/partijen/7260ea01-12c0-4750-8fd1-dfa777818837?expand=digitaleAdressen",
            headers={"Content-Type": "application/json"},
            json={
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            },
        )

        klantcontact = {
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "url": "http://example.com",
            "gingOverOnderwerpobjecten": [],
            "hadBetrokkenActoren": [],
            "omvatteBijlagen": [],
            "hadBetrokkenen": [],
            "leiddeTotInterneTaken": [],
            "nummer": "007",
            "kanaal": "email",
            "onderwerp": "Aanvraag",
            "inhoud": "Hoe gaat het?",
            "taal": "nl",
            "vertrouwelijk": False,
            "plaatsgevondenOp": "2019-08-24T14:15:22Z",
        }
        betrokkene = {
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "url": "http://example.com",
            "wasPartij": {
                "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
                "url": "http://example.com",
            },
            "hadKlantcontact": {
                "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
                "url": "http://example.com",
            },
            "digitaleAdressen": [{}],
            "volledigeNaam": "John Doe",
            "rol": "medewerker",
            "initiator": True,
        }
        interne_taak = {
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "url": "http://example.com",
            "gevraagdeHandeling": "",
            "aanleidinggevendKlantcontact": {
                "uuid": klantcontact["uuid"],
                "url": "http://example.com",
            },
            "status": "te_verwerken",
            "toegewezenOp": "2019-08-24T14:15:22Z",
        }

        self.matchers = [
            m.post(
                "http://localhost:8338/klantinteracties/api/v1/betrokkenen",
                headers={"Content-Type": "application/json"},
                json=betrokkene,
            ),
            m.post(
                "http://localhost:8338/klantinteracties/api/v1/klantcontacten",
                headers={"Content-Type": "application/json"},
                json=klantcontact,
            ),
            m.post(
                "http://localhost:8338/klantinteracties/api/v1/internetaken",
                headers={"Content-Type": "application/json"},
                json=interne_taak,
            ),
        ]

    def install_mocks_openklant_no_bsn_kvk(self, m):
        """Mock OpenKlant2 API calls for users without BSN/KVK - creates partij without identificatoren"""
        # No search is performed for users without BSN/KVK - they are created directly

        # Mock partij creation without identificatoren
        partij = {
            "uuid": "7260ea01-12c0-4750-8fd1-dfa777818837",
            "digitaleAdressen": [
                {
                    "uuid": "d1234567-89ab-cdef-0123-456789abcdef",
                    "adres": "test@example.com",
                    "soortDigitaalAdres": "email",
                    "omschrijving": "E-mailadres",
                    "verstrektDoorBetrokkene": {
                        "uuid": "7260ea01-12c0-4750-8fd1-dfa777818837"
                    },
                }
            ],
            "voorkeursDigitaalAdres": {
                "uuid": "d1234567-89ab-cdef-0123-456789abcdef",
            },
            "indicatieGeheimhouding": False,
            "indicatieActief": True,
            "voorkeurstaal": "nld",
            "soortPartij": "persoon",
            "partijIdentificatie": {
                "contactnaam": {
                    "voorletters": "T.",
                    "voornaam": "Test",
                    "achternaam": "User",
                }
            },
        }

        partij_create_matcher = m.post(
            "http://localhost:8338/klantinteracties/api/v1/partijen",
            headers={"Content-Type": "application/json"},
            json=partij,
            status_code=201,
        )

        # Mock klantcontact creation
        klantcontact = {
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "url": "http://example.com",
            "nummer": "007",
            "kanaal": "webformulier",
            "onderwerp": "Aanvraag",
            "inhoud": "What?",
            "taal": "nl",
            "vertrouwelijk": False,
            "plaatsgevondenOp": "2019-08-24T14:15:22Z",
        }

        klantcontact_create_matcher = m.post(
            "http://localhost:8338/klantinteracties/api/v1/klantcontacten",
            headers={"Content-Type": "application/json"},
            json=klantcontact,
            status_code=201,
        )

        # Mock betrokkene creation
        betrokkene = {
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "url": "http://example.com",
            "wasPartij": {
                "uuid": "7260ea01-12c0-4750-8fd1-dfa777818837",
                "url": "http://example.com",
            },
            "hadKlantcontact": {
                "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
                "url": "http://example.com",
            },
            "rol": "belanghebbende",
            "initiator": True,
        }

        betrokkene_create_matcher = m.post(
            "http://localhost:8338/klantinteracties/api/v1/betrokkenen",
            headers={"Content-Type": "application/json"},
            json=betrokkene,
            status_code=201,
        )

        # Mock interne taak creation
        interne_taak = {
            "uuid": "095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            "url": "http://example.com",
            "gevraagdeHandeling": "Beantwoord de vraag van de klant",
            "aanleidinggevendKlantcontact": {
                "uuid": klantcontact["uuid"],
                "url": "http://example.com",
            },
            "status": "te_verwerken",
            "toegewezenOp": "2019-08-24T14:15:22Z",
        }

        interne_taak_create_matcher = m.post(
            "http://localhost:8338/klantinteracties/api/v1/internetaken",
            headers={"Content-Type": "application/json"},
            json=interne_taak,
            status_code=201,
        )

        self.matchers = [
            partij_create_matcher,
            klantcontact_create_matcher,
            betrokkene_create_matcher,
            interne_taak_create_matcher,
        ]

    def install_mocks_digid_missing_contact_info(self, m) -> "MockAPICreateData":
        self.matchers = [
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
                json=paginated_response([self.klant_bsn_no_contact_info]),
            ),
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant_bsn_no_contact_info,
                status_code=200,
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}contactmomenten",
                json=self.contactmoment,
                status_code=201,
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten",
                json=self.klant_contactmoment,
                status_code=201,
            ),
        ]
        return self

    def install_mocks_eherkenning(self, m, use_rsin=True) -> "MockAPICreateData":
        if use_rsin:
            first_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.rsin}",
                json=paginated_response([self.klant_bsn]),
            )
        else:
            first_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
                json=paginated_response([self.klant_bsn]),
            )

        self.matchers = [
            first_matcher,
            m.post(
                f"{CONTACTMOMENTEN_ROOT}contactmomenten",
                json=self.contactmoment,
                status_code=201,
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten",
                json=self.klant_contactmoment,
                status_code=201,
            ),
        ]
        return self

    def install_mocks_eherkenning_missing_contact_info(
        self, m, use_rsin=True
    ) -> "MockAPICreateData":
        if use_rsin:
            first_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.rsin}",
                json=paginated_response([self.klant_eherkenning_no_contact_info]),
            )
        else:
            first_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
                json=paginated_response([self.klant_eherkenning_no_contact_info]),
            )

        self.matchers = [
            first_matcher,
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant_bsn,
                status_code=200,
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}contactmomenten",
                json=self.contactmoment,
                status_code=201,
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten",
                json=self.klant_contactmoment,
                status_code=201,
            ),
        ]
        return self
