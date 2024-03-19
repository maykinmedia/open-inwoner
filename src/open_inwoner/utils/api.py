import logging
from datetime import datetime
from ipaddress import IPv4Address
from typing import Any

import requests

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
    """
    Mixin for `pydantic.BaseModel` to make `BaseModel.dict()` produce JSON serialized data
    """

    # To make `BaseModel.dict()` produce JSON serialized data, i.e. for usage in tests
    # in tandem with `requests_mock`, we cast the data using the configured JSON encoders
    # Source: https://github.com/pydantic/pydantic/issues/1409#issuecomment-1381655025
    def _iter(self, **kwargs):
        for key, value in super()._iter(**kwargs):
            yield key, self.__config__.json_encoders.get(type(value), lambda v: v)(
                value
            )

    class Config:
        json_encoders = {
            # We need to specify a serializable format for datetimes and IPv4Addresses, otherwise
            # `BaseModel.dict()` will complain about certain types not being JSON serializable
            datetime: lambda dt: dt.isoformat(sep=" "),
            IPv4Address: str,
        }
