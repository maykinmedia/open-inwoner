from typing import Literal

from pydantic import TypeAdapter
from typing_extensions import TypedDict


class InvalidParam(TypedDict):
    name: str
    code: str
    reason: str


class ErrorResponseBody(TypedDict):
    type: str
    code: str
    title: str
    status: int
    detail: str
    instance: str


class ValidationErrorResponseBody(ErrorResponseBody):
    status: Literal[400]
    invalidParams: list[InvalidParam]


ErrorResponseBodyValidator = TypeAdapter(ErrorResponseBody)
ValidationErrorResponseBodyValidator = TypeAdapter(ValidationErrorResponseBody)
