import json
from pathlib import Path

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, JsonResponse
from django.views import View


def inject_filter_parameter_values(request: HttpRequest, data: dict) -> dict:
    """
    To avoid returning data with hardcoded values that do not match the expected response
    when calling a mock API endpoint with query parameters, inject the value of these
    parameters into the response
    """
    for parameter_key, parameter_value in request.GET.items():
        if "results" in data:
            for entry in data["results"]:
                if parameter_key in entry:
                    entry[parameter_key] = parameter_value
        elif parameter_key in data:
            data[parameter_key] = parameter_value
    return data


class APIMockView(View):
    """
    simple API mock that serves sets of JSON from a directory structure that matches the API structure

    ./apimock/api/openklant-read/klanten/klant/aabbaacc.json -> http://server/apimock/openklant-read/klanten/klant/aabbaacc

    with URL transformer
    """

    # TODO move replacers to config file in set directory
    url_replacers = [
        ("https://contactmomenten.nl/api/v1/", "contactmomenten"),
        ("https://klanten.nl/api/v1/", "klanten"),
    ]

    def get(self, request, *args, **kwargs):
        set_name = kwargs["set_name"]
        api_name = kwargs["api_name"]
        endpoint = kwargs["endpoint"]

        endpoint = endpoint.rstrip("/")

        # grab source dir
        base_dir = Path(__file__).parent.resolve()
        base_dir /= "apis"

        api_dir = base_dir / set_name / api_name
        if not api_dir.exists():
            raise Http404("bad api_dir")

        file_path = (api_dir / (endpoint + ".json")).resolve()

        if base_dir not in file_path.parents:
            raise PermissionDenied("bad traversal")

        if not file_path.exists():
            raise Http404("bad endpoint")

        # make dynamic from url conf?
        prefix = request.build_absolute_uri(f"/apimock/{set_name}/")

        with open(file_path) as f:
            data = inject_filter_parameter_values(request, json.load(f))
            process_urls(data, prefix, self.url_replacers)
            return JsonResponse(data, safe=False)


def process_urls(data, prefix, url_replacers):
    """
    recursive replace URL prefixes
    """
    if isinstance(data, list):
        for i, e in enumerate(data):
            data[i] = process_urls(e, prefix, url_replacers)
        return data
    elif isinstance(data, dict):
        for k, e in data.items():
            data[k] = process_urls(e, prefix, url_replacers)
        return data
    elif isinstance(data, str):
        return replace_url_prefix(data, prefix, url_replacers)
    else:
        return data


def replace_url_prefix(s, prefix, url_replacers):
    for url, api_name in url_replacers:
        if s.startswith(url):
            return f"{prefix}{api_name}/{s[len(url) :]}"
    return s
