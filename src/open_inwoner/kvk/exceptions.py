import contextlib
from typing import Self

from requests import Response


class KVKAPIException(Exception):
    response: Response | None
    message: str

    def __init__(self, message=None, *, response: Response | None = None):
        super().__init__()
        self.message = (
            message or "An error occurred while communicating with the KVK API"
        )
        self.response = response

    @classmethod
    def from_error_response(cls, response: Response) -> Self:
        api_error_message: str | None = None

        with contextlib.suppress(BaseException):
            data = response.json()
            api_error_message = data.get("fout", [{}])[0].get("omschrijving", "")

        return cls(message=api_error_message, response=response)
