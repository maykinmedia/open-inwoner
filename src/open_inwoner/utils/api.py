import logging
from typing import Any, Dict, List, Union
from urllib.parse import parse_qs, urlparse

import requests
from ape_pie.client import APIClient

logger = logging.getLogger(__name__)

Object = Dict[str, Any]


class ClientError(Exception):
    pass


# TODO `get_paginated_results` from zgw-consumers==0.28.0 is not compatible with
# `ape_pie.APIClient` because it uses `client.list`
# this change should be added to zgw-consumers at some point
def get_paginated_results(
    client, resource, minimum=None, test_func=None, *args, **kwargs
) -> list:
    request_kwargs = kwargs.get("request_kwargs", {})
    request_params = request_kwargs.get("params", {})

    results = []

    response = client.get(resource, *args, **kwargs)

    def _get_results(response):
        _results = response["results"]
        if test_func:
            _results = [result for result in _results if test_func(result)]
        return _results

    response = response
    results += _get_results(response)

    if minimum and len(results) >= minimum:
        return results

    while response.get("next"):
        next_url = urlparse(response["next"])
        query = parse_qs(next_url.query)
        new_page = int(query["page"][0])

        request_params["page"] = [new_page]
        request_kwargs["params"] = request_params
        kwargs["request_kwargs"] = request_kwargs

        response = client.get(resource, *args, **kwargs)
        results += _get_results(response)

        if minimum and len(results) >= minimum:
            return results

    return results


class JSONParserClient(APIClient):
    """
    Simple layer on top of `ape_pie.APIClient` to attempt to convert the response to
    JSON and check that the request is successful (and raise the correct exceptions if not)
    """

    def request(
        self,
        *args,
        **kwargs,
    ) -> Union[List[Object], Object]:
        response = super().request(*args, **kwargs)
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
