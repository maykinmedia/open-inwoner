import logging
from datetime import datetime
from ipaddress import IPv4Address
from typing import Any

import requests
from pydantic_core import Url

logger = logging.getLogger(__name__)

Object = dict[str, Any]


class ClientError(Exception):
    pass


def get_json_response(response: requests.Response) -> dict | None:
    try:
        response_json = response.json()
    except Exception:
        response_json = None

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        if response.status_code >= 500:
            raise
        raise ClientError(response_json) from exc

    return response_json


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
            Url: str,
        }
        result = super().model_dump(**kwargs)
        for key, value in result.items():
            if mapping_func := json_encoders.get(type(value)):
                result[key] = mapping_func(value)
        return result
