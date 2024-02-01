import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

Object = Dict[str, Any]


class ClientError(Exception):
    pass


def get_json_response(response: requests.Response) -> Optional[dict]:
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
