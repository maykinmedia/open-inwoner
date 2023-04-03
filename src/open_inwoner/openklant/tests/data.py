from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.test import paginated_response

KLANTEN_ROOT = "https://klanten.nl/api/v1/"
CONTACTMOMENTEN_ROOT = "https://contactmomenten.nl/api/v1/"


class MockAPIData:
    def __init__(self):
        self.user = DigidUserFactory(
            bsn="100000001",
        )

        self.klant = generate_oas_component(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        self.contactmoment = generate_oas_component(
            "cmc",
            "schemas/ContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
        )
        self.klant_contactmoment = generate_oas_component(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant["url"],
            contactmoment=self.contactmoment["url"],
        )

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

    def setUpOASMocks(self, m):
        mock_service_oas_get(m, KLANTEN_ROOT, "kc")
        mock_service_oas_get(m, CONTACTMOMENTEN_ROOT, "cmc")

    def install_mocks(self, m) -> "MockAPIData":
        self.setUpOASMocks(m)

        for resource_attr in [
            "klant",
            "contactmoment",
            "klant_contactmoment",
        ]:
            resource = getattr(self, resource_attr)
            m.get(resource["url"], json=resource)

        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
            json=paginated_response([self.klant]),
        )

        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={self.klant['url']}",
            json=paginated_response([self.klant_contactmoment]),
        )

        return self
