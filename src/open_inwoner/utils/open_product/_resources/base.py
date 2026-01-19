from typing import Any, Mapping

from ape_pie import APIClient


class ResourceMixin:
    """Base mixin for OpenProduct API resources."""

    http_client: APIClient

    def __init__(self, http_client: APIClient):
        self.http_client = http_client

    @staticmethod
    def _process_params(params: Mapping | None) -> None | Mapping:
        """
        Process query parameters for the API request.

        Converts list values to comma-separated strings if needed.
        """
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
    ):
        """Make a GET request to the API."""
        return self.http_client.request(
            "get", path, headers=headers, params=self._process_params(params)
        )

    def _post(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ):
        """Make a POST request to the API."""
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
    ):
        """Make a PUT request to the API."""
        return self.http_client.request(
            "put", path, headers=headers, json=data, params=self._process_params(params)
        )

    def _patch(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
        data: Any = None,
    ):
        """Make a PATCH request to the API."""
        return self.http_client.request(
            "patch",
            path,
            headers=headers,
            params=self._process_params(params),
            json=data,
        )

    def _delete(
        self,
        path: str,
        headers: Mapping | None = None,
        params: Mapping | None = None,
    ):
        """Make a DELETE request to the API."""
        return self.http_client.request(
            "delete",
            path,
            headers=headers,
            params=self._process_params(params),
        )
