from ape_pie import APIClient

from openklant._resources import Actor, Betrokkene, DigitaalAdres, Partij


class OpenKlantClient:
    http_client: APIClient

    actor: Actor
    betrokkene: Betrokkene
    digitaal_adres: DigitaalAdres
    partij: Partij

    def __init__(self, token: str):
        self.http_client = APIClient(
            request_kwargs={"headers": {"Authorization": f"Token {token}"}},
            base_url="http://localhost:8000/klantinteracties/api/v1",
        )
        self.actor = Actor(self.http_client)
        self.betrokkene = Betrokkene(self.http_client)
        self.digitaal_adres = DigitaalAdres(self.http_client)
        self.partij = Partij(self.http_client)
