from ape_pie import APIClient

from openklant2._resources.digitaal_adres import DigitaalAdresResource
from openklant2._resources.klant_contact import KlantContactResource
from openklant2._resources.partij import PartijResource
from openklant2._resources.partij_identificator import PartijIdentificatorResource


class OpenKlant2Client:
    http_client: APIClient
    partij: PartijResource

    def __init__(self, token: str, api_root: str):
        self.http_client = APIClient(
            request_kwargs={"headers": {"Authorization": f"Token {token}"}},
            base_url=api_root,
        )

        self.partij = PartijResource(self.http_client)
        self.partij_identificator = PartijIdentificatorResource(self.http_client)
        self.digitaal_adres = DigitaalAdresResource(self.http_client)
        self.klant_contact = KlantContactResource(self.http_client)
