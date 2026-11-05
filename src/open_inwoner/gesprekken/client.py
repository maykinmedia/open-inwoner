import requests
from zgw_consumers.client import build_client

from open_inwoner.utils.api import APIError, BaseAPIClient

from .models import MijnGesprekkenConfig

UPLOAD_TIMEOUT = 60


class GesprekkenAPIError(APIError):
    pass


def uuid_from_url(url: str | None) -> str | None:
    """The uuid of a resource: the last segment of its URL. References are URLs."""
    return url.rstrip("/").rsplit("/", 1)[-1] if url else None


class GesprekkenClient(BaseAPIClient):
    """Client for a Gesprekken API (draft MijnGesprekken standard)."""

    network_error_type = GesprekkenAPIError
    client_error_type = GesprekkenAPIError
    server_error_type = GesprekkenAPIError
    invalid_json_error_type = GesprekkenAPIError
    data_error_type = GesprekkenAPIError

    def list_for_zaak(self, zaak_url: str) -> list[dict]:
        """
        All gesprekken with this zaak as aanleiding, following the next links
        (cursor pagination; the filters are in the link).
        """
        results = []
        params = {"aanleidingZaak": zaak_url}
        url = "gesprekken"
        while url:
            response = self.get(url, params=params)
            self.raise_for_status(response)
            data = self.parse_json(response)
            results.extend(data.get("results", []))
            url, params = data.get("next"), None
        return results

    def open_event_stream(self, last_event_id: str | None, timeout: float):
        """
        Opens GET /events (Server-Sent Events). The caller reads the response with
        `iter_lines()` and closes it.
        """
        headers = {"Accept": "text/event-stream"}
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id
        response = self.get("events", headers=headers, stream=True, timeout=timeout)
        self.raise_for_status(response)
        return response

    def feed_cursor(self) -> str:
        """
        The current position in the event stream: the Feed-Cursor of a snapshot.
        A one-result page is enough, only the header is used.
        """
        response = self.get("gesprekken", params={"pageSize": 1})
        self.raise_for_status(response)
        cursor = response.headers.get("Feed-Cursor")
        if cursor is None:
            raise GesprekkenAPIError("snapshot has no Feed-Cursor header")
        return cursor

    def get_gesprek(self, uuid: str) -> dict:
        response = self.get(f"gesprekken/{uuid}")
        self.raise_for_status(response)
        return self.parse_json(response)

    def create_gesprek(self, data: dict) -> dict:
        response = self.post("gesprekken", json=data)
        self.raise_for_status(response)
        return self.parse_json(response)

    def eindig_gesprek(self, uuid: str) -> dict:
        response = self.post(f"gesprekken/{uuid}/eindigen")
        self.raise_for_status(response)
        return self.parse_json(response)

    def create_bijdrage(self, data: dict) -> dict:
        response = self.post("gespreksbijdragen", json=data)
        self.raise_for_status(response)
        return self.parse_json(response)

    def create_upload_sessie(self, data: dict) -> dict:
        response = self.post("bestanden/upload-sessie", json=data)
        self.raise_for_status(response)
        return self.parse_json(response)

    def get_bestand(self, file_id: str) -> dict:
        response = self.get(f"bestanden/{file_id}")
        self.raise_for_status(response)
        return self.parse_json(response)

    def mark_gelezen(self, bijdrage_uuid: str, deelname_url: str) -> dict:
        response = self.post(
            f"gespreksbijdragen/{bijdrage_uuid}/gelezen",
            json={"gespreksdeelname": deelname_url},
        )
        self.raise_for_status(response)
        return self.parse_json(response)


def put_bestand(upload_url: str, bestand, content_type: str) -> None:
    """
    Sends the file to the pre-signed URL of an upload-sessie. This is the storage,
    not the API: outside the API client, so no API credentials go along. The URL is
    a secret until it expires, so it stays out of the errors, which end up in logs.
    """
    bestand.seek(0)
    try:
        response = requests.put(
            upload_url,
            data=bestand,
            headers={"Content-Type": content_type},
            timeout=UPLOAD_TIMEOUT,
        )
    except requests.RequestException:
        raise GesprekkenAPIError("upload to storage failed") from None
    if not response.ok:
        raise GesprekkenAPIError(
            "storage refused the upload", status_code=response.status_code
        )


def build_gesprekken_client(
    config: MijnGesprekkenConfig | None = None,
) -> GesprekkenClient | None:
    config = config or MijnGesprekkenConfig.get_solo()
    if not config.service:
        return None
    return build_client(config.service, client_factory=GesprekkenClient)
