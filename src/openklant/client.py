from ape_pie import APIClient

from openklant._resources import Partij


class OpenKlantClient:
    http_client: APIClient

    def __init__(self, token: str):
        self.http_client = APIClient(
            request_kwargs={"headers": {"Authorization": f"Token {token}"}},
            base_url="http://localhost:8000/klantinteracties/api/v1",
        )
        self.partij = Partij(self.http_client)

    partij: Partij
