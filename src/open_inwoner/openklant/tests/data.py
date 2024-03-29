from requests.exceptions import RequestException
from zgw_consumers.constants import APITypes

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.utils.test import paginated_response

KLANTEN_ROOT = "https://klanten.nl/api/v1/"
CONTACTMOMENTEN_ROOT = "https://contactmomenten.nl/api/v1/"
ZAKEN_ROOT = "https://zaken.nl/api/v1/"


class MockAPIData:
    @classmethod
    def setUpServices(cls):
        config = OpenKlantConfig.get_solo()
        config.klanten_service = ServiceFactory(
            api_root=KLANTEN_ROOT, api_type=APITypes.kc
        )
        config.contactmomenten_service = ServiceFactory(
            api_root=CONTACTMOMENTEN_ROOT, api_type=APITypes.cmc
        )
        config.save()

        oz_config = OpenZaakConfig.get_solo()
        oz_config.zaak_service = ServiceFactory(
            api_root=ZAKEN_ROOT, api_type=APITypes.zrc
        )
        oz_config.save()


class MockAPIReadPatchData(MockAPIData):
    def __init__(self):
        self.user = DigidUserFactory(
            email="old@example.com",
            phonenumber="0100000000",
        )
        self.eherkenning_user = eHerkenningUserFactory(
            email="old2@example.com",
            kvk="12345678",
            rsin="000000000",
        )

        self.klant_old = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="bad@example.com",
            telefoonnummer="",
        )
        self.klant_updated = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="good@example.com",
            telefoonnummer="0123456789",
        )

    def install_mocks(self, m) -> "MockAPIReadPatchData":
        self.matchers = [
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
                json=paginated_response([self.klant_old]),
            ),
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant_updated,
                status_code=200,
            ),
        ]
        return self

    def install_mocks_eherkenning(self, m, use_rsin=True) -> "MockAPIReadPatchData":
        if use_rsin:
            first_eherkenning_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.rsin}",
                json=paginated_response([self.klant_old]),
            )
        else:
            first_eherkenning_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
                json=paginated_response([self.klant_old]),
            )
        self.matchers = [
            first_eherkenning_matcher,
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant_updated,
                status_code=200,
            ),
        ]
        return self


class MockAPIReadData(MockAPIData):
    def __init__(self):
        self.user = DigidUserFactory(
            bsn="100000001",
        )
        self.eherkenning_user = eHerkenningUserFactory(
            kvk="12345678",
            rsin="000000000",
        )

        self.klant = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="foo@example.com",
            telefoonnummer="0612345678",
        )
        self.klant2 = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            emailadres="foo@bar.com",
            telefoonnummer="0687654321",
        )
        self.klant_vestiging = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            url=f"{KLANTEN_ROOT}klant/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            emailadres="foo@bar.com",
            telefoonnummer="0612345678",
        )
        self.contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/ContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            identificatie="AB123",
            type="SomeType",
            kanaal="MAIL",
            status=Status.afgehandeld,
            antwoord="foo",
            onderwerp="e_suite_subject_code",
            registratiedatum="2022-01-01T12:00:00Z",
        )
        self.contactmoment2 = generate_oas_component_cached(
            "cmc",
            "schemas/ContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd",
            identificatie="AB123",
            type="SomeType",
            kanaal="MAIL",
            status=Status.afgehandeld,
            antwoord="",
            onderwerp="e_suite_subject_code",
        )
        self.contactmoment_vestiging = generate_oas_component_cached(
            "cmc",
            "schemas/ContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee",
            identificatie="AB123",
            type="SomeType",
            kanaal="MAIL",
            status=Status.afgehandeld,
            antwoord="",
            onderwerp="e_suite_subject_code",
        )
        self.klant_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant["url"],
            contactmoment=self.contactmoment["url"],
        )
        self.klant_contactmoment2 = generate_oas_component_cached(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee",
            klant=self.klant2["url"],
            contactmoment=self.contactmoment2["url"],
        )
        self.klant_contactmoment3 = generate_oas_component_cached(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd",
            klant=self.klant["url"],
            contactmoment=self.contactmoment_vestiging["url"],
        )
        self.klant_contactmoment4 = generate_oas_component_cached(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
            klant=self.klant_vestiging["url"],
            contactmoment=self.contactmoment_vestiging["url"],
        )
        self.objectcontactmoment_other = generate_oas_component_cached(
            "cmc",
            "schemas/ObjectContactMoment",
            uuid="bb51784c-fa2c-4f65-b24e-7179b615efac",
            url=f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten/bb51784c-fa2c-4f65-b24e-7179b615efac",
            object="http://documenten.nl/api/v1/1",
            contactmoment=self.contactmoment["url"],
        )
        # Force objectType other than zaak, to verify that filtering works
        self.objectcontactmoment_other["object_type"] = "document"
        self.objectcontactmoment_zaak = generate_oas_component_cached(
            "cmc",
            "schemas/ObjectContactMoment",
            uuid="77880671-b88a-44ed-ba24-dc2ae688c2ec",
            url=f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten/77880671-b88a-44ed-ba24-dc2ae688c2ec",
            object=f"{ZAKEN_ROOT}zaken/410bb717-ff3d-4fd8-8357-801e5daf9775",
            object_type="zaak",
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
            "klant",
            "klant2",
            "klant_vestiging",
            "contactmoment",
            "contactmoment2",
            "contactmoment_vestiging",
            "klant_contactmoment",
            "klant_contactmoment2",
            "klant_contactmoment3",
            "klant_contactmoment4",
            "zaak",
        ]:
            resource = getattr(self, resource_attr)
            m.get(resource["url"], json=resource)

        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
            json=paginated_response([self.klant]),
        )

        # Mock both RSIN and KvK fetch variations, can be toggled with feature flag
        # `use_rsin_for_innNnpId_query_parameter`
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
            json=paginated_response([self.klant2]),
        )
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.rsin}",
            json=paginated_response([self.klant2]),
        )
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectVestiging__vestigingsNummer=1234",
            json=paginated_response([self.klant_vestiging]),
        )

        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant['url']}",
            json=paginated_response([self.klant_contactmoment]),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant2['url']}",
            json=paginated_response([self.klant_contactmoment2]),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant_vestiging['url']}",
            json=paginated_response([self.klant_contactmoment4]),
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
    def __init__(self):
        self.user = DigidUserFactory(
            bsn="100000001",
        )
        self.eherkenning_user = eHerkenningUserFactory(
            kvk="12345678",
            rsin="000000000",
        )
        self.klant = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            bronorganisatie="123456789",
            voornaam="Foo",
            achternaam="Bar",
            emailadres="foo@example.com",
            telefoonnummer="0612345678",
        )
        self.klant_no_contact_info = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            bronorganisatie="123456789",
            voornaam="Foo",
            achternaam="Bar",
            emailadres="",
            telefoonnummer="",
        )
        self.contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/ContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            # identificatie="AB123",
            # type="SomeType",
            # kanaal="MAIL",
            status=Status.nieuw,
            antwoord="",
            text="hey!\n\nwaddup?",
        )
        self.klant_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant["url"],
            contactmoment=self.contactmoment["url"],
        )

        self.matchers = []

    def install_mocks_anon_with_klant(self, m) -> "MockAPICreateData":
        self.matchers = [
            m.post(f"{KLANTEN_ROOT}klanten", json=self.klant, status_code=201),
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
                json=paginated_response([self.klant]),
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

    def install_mocks_digid_missing_contact_info(self, m) -> "MockAPICreateData":
        self.matchers = [
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
                json=paginated_response([self.klant_no_contact_info]),
            ),
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant,
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
                json=paginated_response([self.klant]),
            )
        else:
            first_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
                json=paginated_response([self.klant]),
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
                json=paginated_response([self.klant_no_contact_info]),
            )
        else:
            first_matcher = m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.kvk}",
                json=paginated_response([self.klant_no_contact_info]),
            )

        self.matchers = [
            first_matcher,
            m.patch(
                f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=self.klant,
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
