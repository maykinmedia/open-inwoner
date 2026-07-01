import json
import subprocess
import time
from pathlib import Path

from django.test import TestCase as DjangoTestCase

import requests
import structlog
from openklant_client import OpenKlantClient
from typing_extensions import TypedDict
from vcr.record_mode import RecordMode
from vcr.unittest import VCRMixin

from open_inwoner.conf.utils import config

logger = structlog.stdlib.get_logger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]


class OpenKlantServiceManager:
    _in_server_context: bool = False
    _django_service_name: str = "openklant-web"
    _api_root: str = "http://localhost:8338"
    _api_path: str = "/klantinteracties/api/v1"
    # Must match the `secret` used by OpenKlant2ConfigFactory's ServiceFactory,
    # since that's the token the client under test actually sends.
    _api_token: str = "test-api-token"
    _docker_compose_project_name: str = "openklant2-api-test"
    _docker_compose_path: Path = _REPO_ROOT / "docker" / "docker-compose.openklant.yml"

    def _docker_compose(self, *args: str, check: bool = True, input: str | None = None):
        input_data = {"text": True, "input": input} if input else {}
        try:
            return subprocess.run(
                args=[
                    "docker",
                    "compose",
                    "-f",
                    str(self._docker_compose_path),
                    "-p",
                    self._docker_compose_project_name,
                    *args,
                ],
                check=check,
                capture_output=True,
                **input_data,
            )
        except subprocess.CalledProcessError as exc:
            logger.exception(
                "Unable to execute command",
                stderr=str(exc.stderr),
                stdout=str(exc.stdout),
            )
            raise

    def _manage_py(self, *args: str, input: str | None = None):
        self._docker_compose(
            "run",
            "--rm",
            self._django_service_name,
            "python",
            "src/manage.py",
            *args,
            input=input,
        )

    def _service_teardown(self):
        self._docker_compose("kill", check=False)
        self._docker_compose("down", "-v")
        self._docker_compose("rm", "-f")

    def _service_init(self):
        self._docker_compose("up", "-d")
        self._wait_for_response()
        self._manage_py("migrate")

    def reset_db_state(self):
        self._manage_py("flush", "--no-input")
        self._load_fixture_from_json_string(self._generate_token_fixture())

    def _load_fixture_from_json_string(self, fixture: str):
        self._manage_py("loaddata", "--format", "json", "-", input=fixture)

    def _generate_token_fixture(self) -> str:
        return json.dumps(
            [
                {
                    "model": "token.tokenauth",
                    "pk": 1,
                    "fields": {
                        "identifier": "test-token",
                        "token": self._api_token,
                        "contact_person": "Boaty McBoatface",
                        "email": "boaty@mcboatface.com",
                        "organization": "",
                        "last_modified": "2024-08-22T07:43:21.837Z",
                        "created": "2024-08-22T07:43:21.837Z",
                        "application": "",
                        "administration": "",
                    },
                },
                {
                    "model": "accounts.user",
                    "pk": 1,
                    "fields": {
                        # password is "secret"
                        "password": "pbkdf2_sha256$600000$11HRNvD3J8QPTCkp0avgKX$gY/NX5+Ap8jAmD86HxEneVHwzi9+g45NhTBMkB3vJuo=",
                        "last_login": "2025-01-28T10:30:23.474Z",
                        "is_superuser": True,
                        "username": "admin",
                        "first_name": "",
                        "last_name": "",
                        "email": "admin@oip.nl",
                        "is_staff": True,
                        "is_active": True,
                        "date_joined": "2025-01-28T10:29:59.843Z",
                        "groups": [],
                        "user_permissions": [],
                    },
                },
            ]
        )

    def _wait_for_response(self, interval: float = 0.5, max_wait: float = 60):
        start_time = time.time()
        while True:
            try:
                requests.get(self._api_root)
                return
            except requests.RequestException:
                logger.debug("Exception while checking for liveness", exc_info=True)
                elapsed = time.time() - start_time
                if elapsed > max_wait:
                    raise RuntimeError(
                        f"Maximum wait for service to be healthy exceeded: {elapsed} > {max_wait}"
                    ) from None
                time.sleep(interval)

    def setUp(self):
        if self._in_server_context:
            raise RuntimeError(
                "You cannot have multiple server contexts active at the same time"
            )
        self._in_server_context = True
        self._service_teardown()
        self._service_init()

    def tearDown(self):
        self._service_teardown()
        self._in_server_context = False

    def client_factory(self) -> OpenKlantClient:
        return OpenKlantClient(
            base_url=f"{self._api_root}{self._api_path}",
            token=self._api_token,
        )


class LiveOpenKlantTestMixin:
    _service: OpenKlantServiceManager

    @classmethod
    def should_bypass_live_server(cls) -> bool:
        raise NotImplementedError

    @property
    def openklant_client(self) -> OpenKlantClient:
        return self._service.client_factory()

    def reset_db(self):
        if not self.should_bypass_live_server():
            self._service.reset_db_state()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._service = OpenKlantServiceManager()
        if not cls.should_bypass_live_server():
            cls._service.setUp()

    @classmethod
    def tearDownClass(cls):
        if not cls.should_bypass_live_server():
            cls._service.tearDown()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.reset_db()


class OpenKlant2ServiceTestConfig(TypedDict):
    use_live_service: bool
    vcr_record_mode: RecordMode


class Openklant2ServiceTestCase(VCRMixin, LiveOpenKlantTestMixin, DjangoTestCase):
    vcr_record_mode: RecordMode = RecordMode.NONE

    @classmethod
    def get_config(cls) -> OpenKlant2ServiceTestConfig:
        record_openklant_cassettes = config("RECORD_OPENKLANT_CASSETTES", default=False)
        return {
            "use_live_service": record_openklant_cassettes,
            "vcr_record_mode": (
                RecordMode.ALL if record_openklant_cassettes else cls.vcr_record_mode
            ),
        }

    @classmethod
    def should_bypass_live_server(cls) -> bool:
        return not cls.get_config()["use_live_service"]

    def _get_vcr(self, **kwargs):
        vcr = super()._get_vcr(**kwargs)
        vcr.record_mode = self.get_config()["vcr_record_mode"]
        vcr.match_on = ["method", "scheme", "host", "port", "path", "query"]
        return vcr
