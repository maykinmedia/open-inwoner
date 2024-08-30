import json
from typing import Any, Dict, List, Mapping, MutableMapping, TypeGuard, TypeVar, Union

import pydantic
import requests
from ape_pie import APIClient

from openklant._resources.error import (
    ErrorResponseBodyValidator,
    ValidationErrorResponseBodyValidator,
)
from openklant.exceptions import BadRequest, ClientError, GenericErrorResponse, NotFound

T = TypeVar("T")

ResourceResponse = MutableMapping[str, Any]


JSONPrimitive = Union[str, int, None, float]
JSONValue = Union[JSONPrimitive, "JSONObject", List["JSONValue"]]
JSONObject = Dict[str, JSONValue]


class ResourceMixin:
    http_client: APIClient

    def __init__(self, http_client: APIClient):
        self.http_client = http_client

    def process_response(self, response: requests.Response) -> TypeGuard[JSONValue]:
        response_data = None
        try:
            response_data = response.json()
        except (requests.exceptions.JSONDecodeError, json.JSONDecodeError):
            pass

        match response.status_code:
            case code if code >= 200 and code < 300 and response_data:
                return response_data
            case code if code >= 400 and code < 500 and response_data:
                match code:
                    case 400:
                        validator = ValidationErrorResponseBodyValidator
                        exc_class = BadRequest
                    case 404:
                        validator = ErrorResponseBodyValidator
                        exc_class = NotFound
                    case _:
                        validator = ErrorResponseBodyValidator
                        exc_class = ClientError

                try:
                    validator.validate_python(response_data)
                    raise exc_class(response_data)
                except pydantic.ValidationError:
                    raise GenericErrorResponse()
            case _:
                raise GenericErrorResponse()

        raise

    def _get(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
    ) -> requests.Response:
        with self.http_client as client:
            return client.request("get", path, headers=headers, params=params)

    def _post(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ) -> requests.Response:
        with self.http_client as client:
            return client.request(
                "post", path, headers=headers, json=data, params=params
            )

    def _put(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ) -> requests.Response:
        with self.http_client as client:
            return client.request(
                "put", path, headers=headers, json=data, params=params
            )

    def _delete(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
    ) -> requests.Response:
        with self.http_client as client:
            return client.request(
                "delete",
                path,
                headers=headers,
                params=params,
            )

    def _patch(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ) -> requests.Response:
        with self.http_client as client:
            return client.request(
                "patch",
                path,
                headers=headers,
                params=params,
                json=data,
            )

    def _options(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
    ) -> requests.Response:
        with self.http_client as client:
            return client.request(
                "delete",
                path,
                headers=headers,
                params=params,
            )
