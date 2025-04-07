from pathlib import Path

import pytest

from openklant2.tests.helpers import OpenKlantServiceManager


def pytest_addoption(parser):
    parser.addoption(
        "--with-openklant-service",
        action="store_true",
        default=False,
        help="Whether to seed a fresh OpenKlant Docker instance for each test",
    )


@pytest.fixture(scope="session", autouse=True)
def openklant_service_singleton(request):
    # Depending on whether we're working with a live service or not, we either
    # spawn the service and yield the running service, or simply return a
    # regular instance for the purposes of using the client factory in the
    # client fixture. We split the fixtures up because the service singleton
    # should be session-scoped, spawning the service at the start of the run
    # and tearing it down at completion of the run.
    #
    # The client fixture below, by cotrast, should reset the database state for each test.
    service = OpenKlantServiceManager()
    if request.config.getoption("--with-openklant-service"):
        with service.live_service() as running_service:
            yield running_service
    else:
        yield service


@pytest.fixture()
def client(request, openklant_service_singleton: OpenKlantServiceManager):
    if request.config.getoption("--with-openklant-service"):
        # We're running against a live server: clean the state for the test
        with openklant_service_singleton.clean_state() as client:
            yield client
    else:
        # We're running in VCR mode: simply return a client
        yield openklant_service_singleton.client_factory()


@pytest.fixture(scope="session")
def vcr_config():
    return {
        "match_on": [
            "method",
            "scheme",
            "host",
            "port",
            "path",
            "query",
            # "body",
        ],
        "path_transformer": lambda path: Path(str(path).lower()).__str__(),
        "cassette_library_dir": "tests/cassettes",  # adjust this path as needed
    }


def lowercase_cassette_name(function_name):
    """Convert function name to lowercase for VCR cassette names"""
    return function_name.lower()


@pytest.fixture
def vcr_cassette_name(request):
    """Override the default cassette name to ensure it's lowercase"""
    test_name = request.node.name
    # Convert to lowercase and replace any special characters if needed
    return lowercase_cassette_name(test_name)
