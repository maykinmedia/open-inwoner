import pytest

from openklant2.models import OpenKlant2Config
from openklant2.tests.helpers import OpenKlantServiceManager


def pytest_addoption(parser):
    parser.addoption(
        "--with-openklant-service",
        action="store_true",
        default=False,
        help="Whether to seed a fresh OpenKlant Docker instance for each test",
    )


@pytest.fixture(scope="session")
def openklant2_config():
    return OpenKlant2Config(
        api_root="http://localhost:8338",
        api_path="/klantinteracties/api/v1",
        api_token="b2eb1da9861da88743d72a3fb4344288fe2cba44",
        mijn_vragen_kanaal="oip_mijn_vragen",
        mijn_vragen_organisatie_naam="Open Inwoner Platform",
    )


@pytest.fixture(scope="session", autouse=True)
def openklant_service_singleton(request, openklant2_config):
    # Depending on whether we're working with a live service or not, we either
    # spawn the service and yield the running service, or simply return a
    # regular instance for the purposes of using the client factory in the
    # client fixture. We split the fixtures up because the service singleton
    # should be session-scoped, spawning the service at the start of the run
    # and tearing it down at completion of the run.
    #
    # The client fixture below, by cotrast, should reset the database state for each test.
    service = OpenKlantServiceManager(config=openklant2_config)
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
    }
