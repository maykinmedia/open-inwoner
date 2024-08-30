import pytest
from decouple import config

from openklant.client import OpenKlantClient


@pytest.fixture()
def api_token():
    token = config("OPEN_KLANT_TOKEN", None)
    return token


@pytest.fixture()
def client(api_token):
    return OpenKlantClient(api_token)
