import pprint

from openklant._resources.error import (
    ErrorResponseBody,
    InvalidParam,
    ValidationErrorResponseBody,
)


class OpenKlantException(Exception):
    pass


class GenericErrorResponse(OpenKlantException):
    pass


class ClientError(OpenKlantException):

    type: str
    code: str
    title: str
    status: int
    detail: str
    instance: str

    def __init__(self, response: ErrorResponseBody):
        self.type = response["type"]
        self.code = response["code"]
        self.title = response["title"]
        self.status = response["status"]
        self.detail = response["detail"]
        self.instance = response["instance"]

        OpenKlantException.__init__(
            self, f'status={self.status} code={self.code} title="{self.title}"'
        )


class NotFound(ClientError):
    pass


class BadRequest(ClientError):
    invalidParams: list[InvalidParam]

    def __init__(self, response: ValidationErrorResponseBody):
        self.type = response["type"]
        self.code = response["code"]
        self.title = response["title"]
        self.status = response["status"]
        self.detail = response["detail"]
        self.instance = response["instance"]
        self.invalidParams = response["invalidParams"]

        invalid_params_formatted = ""
        if self.invalidParams:
            invalid_params_formatted = "\nInvalid parameters:\n"
            invalid_params_formatted += "\n".join(
                pprint.pformat(param) for param in self.invalidParams
            )

        OpenKlantException.__init__(
            self,
            f'status={self.status} code={self.code} title="{self.title}":{invalid_params_formatted}',
        )
