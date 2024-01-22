from urllib.parse import parse_qs, urlparse


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

    response = response.json()
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
