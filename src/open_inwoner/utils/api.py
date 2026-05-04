from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any

import requests
from ape_pie.client import APIClient
from pydantic_core import Url
from zgw_consumers.api_models.base import factory as _factory

Object = dict[str, Any]


class APIError(Exception):
    pass


class BaseAPIClient(APIClient):
    """
    Base class for APIClient subclasses that maps requests exceptions and HTTP errors
    to domain-specific exceptions configured on the class.
    """

    network_error_type: type[Exception] = APIError
    client_error_type: type[Exception] = APIError
    server_error_type: type[Exception] = APIError
    invalid_json_error_type: type[Exception] = APIError
    data_error_type: type[Exception] = APIError

    def request(self, *args, **kwargs):
        try:
            return super().request(*args, **kwargs)
        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.TooManyRedirects,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ContentDecodingError,
        ) as exc:
            raise self.network_error_type(str(exc)) from exc

    def raise_for_status(self, response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if response.status_code >= 500:
                raise self.server_error_type(str(exc)) from exc
            raise self.client_error_type(str(exc)) from exc

    def parse_json(self, response) -> dict:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise self.invalid_json_error_type(str(exc)) from exc

    def factory(self, model, data):
        try:
            return _factory(model, data)
        except (TypeError, ValueError, KeyError) as exc:
            raise self.data_error_type(str(exc)) from exc


class JSONEncoderMixin:
    def model_dump(self, **kwargs):
        """
        To make `BaseModel.model_dump()` produce JSON serialized data, i.e. for usage in tests
        in tandem with `requests_mock`, we cast the data using the configured JSON encoders
        Source: https://github.com/pydantic/pydantic/issues/1409#issuecomment-1130601015
        """
        json_encoders: dict = {
            datetime: lambda dt: dt.isoformat(sep=" "),
            IPv4Address: str,
            IPv6Address: str,
            Url: str,
        }
        result = super().model_dump(**kwargs)
        for key, value in result.items():
            if mapping_func := json_encoders.get(type(value)):
                result[key] = mapping_func(value)
        return result
