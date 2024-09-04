import pprint
from typing import Literal, cast

from requests import Response

from openklant2.types.error import (
    ErrorResponseBody,
    InvalidParam,
    ValidationErrorResponseBody,
)


class OpenKlant2Exception(Exception):
    """Base exception for all client-related errors."""

    pass


class ResponseError(OpenKlant2Exception):
    """A response was received, but it was erroneous in some aspect."""

    response: Response

    def __init__(self, response: Response, msg: str):
        self.response = response
        super().__init__(msg)


class NonJSONResponse(ResponseError):
    """Response was unexpectedly not in JSON."""

    def __init__(self, response: Response):
        super().__init__(
            response,
            f"The content type of this response was {response.headers.get('Content-Type')}, but "
            " application/json was expected.",
        )


class InvalidJSONResponse(ResponseError):
    """Response was marked as JSON but contained malformed content."""

    def __init__(self, response: Response):
        super().__init__(
            response,
            "The response content-type was marked as JSON, but cannot be decoded",
        )


class StructuredErrorResponse(ResponseError):
    """An error response with a well-known JSON object describing the error."""

    type: str
    code: str
    title: str
    status: int
    detail: str
    instance: str

    def __init__(self, response: Response, body: ErrorResponseBody):
        self.type = body["type"]
        self.code = body["code"]
        self.title = body["title"]
        self.status = body["status"]
        self.detail = body["detail"]
        self.instance = body["instance"]

        super().__init__(
            response,
            f'status={self.status} code={self.code} title="{self.title}"',
        )


class ClientError(StructuredErrorResponse):
    pass


class BadRequest(ClientError):
    code: Literal[400]
    invalidParams: list[InvalidParam]

    def __init__(self, response: Response, body: ValidationErrorResponseBody):
        self.invalidParams = body["invalidParams"]

        invalid_params_formatted = ""
        if self.invalidParams:
            invalid_params_formatted = "\nInvalid parameters:\n"
            invalid_params_formatted += "\n".join(
                pprint.pformat(param) for param in self.invalidParams
            )

        StructuredErrorResponse.__init__(
            self,
            response,
            cast(ErrorResponseBody, body),
        )
        OpenKlant2Exception.__init__(
            self,
            f'status={body["status"]} code={body["status"]} title="{body["title"]}":{invalid_params_formatted}',
        )


class NotFound(ClientError):
    code: Literal[404]


class Unauthorized(ClientError):
    code: Literal[401]


class Forbidden(ClientError):
    code: Literal[403]
