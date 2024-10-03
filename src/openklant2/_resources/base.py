import json
from typing import Any, Dict, List, Mapping, MutableMapping, TypeGuard, Union

import pydantic
import requests
from ape_pie import APIClient

from openklant2.exceptions import (
    BadRequest,
    Forbidden,
    InvalidJSONResponse,
    NonJSONResponse,
    NotFound,
    ResponseError,
    StructuredErrorResponse,
    Unauthorized,
)
from openklant2.types.error import (
    ErrorResponseBodyValidator,
    ValidationErrorResponseBodyValidator,
)

ResourceResponse = MutableMapping[str, Any]


JSONPrimitive = Union[str, int, None, float]
JSONValue = Union[JSONPrimitive, "JSONObject", List["JSONValue"]]
JSONObject = Dict[str, JSONValue]


class ResourceMixin:
    http_client: APIClient

    def __init__(self, http_client: APIClient):
        self.http_client = http_client

    @staticmethod
    def process_response(response: requests.Response) -> TypeGuard[JSONValue]:
        response_data = None
        try:
            content_type = response.headers.get("Content-Type", "")
            # Note: there are currently no non-JSON responses defined in the
            # spec, the obvious example would be e.g. something like a blob
            # download. Until such endpoints are encountered, we treat non-JSON
            # as an error.
            if not content_type.lower().startswith("application/json"):
                raise NonJSONResponse(response)

            response_data = response.json()
        except (requests.exceptions.JSONDecodeError, json.JSONDecodeError):
            raise InvalidJSONResponse(response)

        match response.status_code:
            case code if code >= 200 and code < 300 and response_data:
                return response_data
            case code if code >= 400 and code < 500 and response_data:
                validator = ErrorResponseBodyValidator
                exc_class = StructuredErrorResponse
                match code:
                    case 400:
                        validator = ValidationErrorResponseBodyValidator
                        exc_class = BadRequest
                    case 401:
                        exc_class = Unauthorized
                    case 403:
                        exc_class = Forbidden
                    case 404:
                        exc_class = NotFound
                    case _:
                        pass

                try:
                    validator.validate_python(response_data)
                    raise exc_class(response, response_data)
                except pydantic.ValidationError:
                    # JSON body, but not in an expected schema. Fall through to generic ErrorResponse
                    pass
            case _:
                pass

        raise ResponseError(response, msg="Error response")

    @staticmethod
    def _process_params(params: Mapping | None) -> None | Mapping:
        # The default approach to serializing lists in the requests library is
        # not supported by OpenKlant 2. See:
        # https://github.com/maykinmedia/open-klant/issues/250
        if params is None:
            return params

        transposed_params = dict(params)
        for key, val in params.items():
            if isinstance(val, list):
                transposed_params[key] = ",".join(str(element) for element in val)

        return transposed_params

    def _get(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
    ) -> requests.Response:

        return self.http_client.request(
            "get", path, headers=headers, params=self._process_params(params)
        )

    def _post(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ) -> requests.Response:
        return self.http_client.request(
            "post",
            path,
            headers=headers,
            json=data,
            params=self._process_params(params),
        )

    def _put(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ) -> requests.Response:
        return self.http_client.request(
            "put", path, headers=headers, json=data, params=self._process_params(params)
        )

    def _delete(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
    ) -> requests.Response:
        return self.http_client.request(
            "delete",
            path,
            headers=headers,
            params=self._process_params(params),
        )

    def _patch(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ) -> requests.Response:
        return self.http_client.request(
            "patch",
            path,
            headers=headers,
            params=self._process_params(params),
            json=data,
        )

    def _options(
        self,
        path: str,
        headers: Mapping | None = None,
        params: MutableMapping | None = None,
    ) -> requests.Response:
        return self.http_client.request(
            "delete",
            path,
            headers=headers,
            params=self._process_params(params),
        )
