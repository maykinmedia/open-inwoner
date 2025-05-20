from typing import Self

from requests import Response


class KVKAPIException(Exception):
    def __init__(self, message=None):
        super().__init__(message)
        self.message = message

    @classmethod
    def from_error_response(cls, response: Response) -> Self:
        try:
            data = response.json()
        except Exception:
            api_error_message = ""
        else:
            api_error_message = data.get("fout", [{}])[0].get("omschrijving", "")
        cls.message = api_error_message

        return cls(message=api_error_message)
