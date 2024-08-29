import pytest

from openklant.client import OpenKlantClient


@pytest.fixture()
def api_token():
    return "b2eb1da9861da88743d72a3fb4344288fe2cba44"


@pytest.fixture()
def client(api_token):
    return OpenKlantClient(api_token)
