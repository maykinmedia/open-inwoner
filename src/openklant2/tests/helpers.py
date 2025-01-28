import json
import logging
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urljoin

import requests

from openklant2.client import OpenKlant2Client

BASE_DIR = Path(__file__).parent.parent.resolve()

logger = logging.getLogger(__name__)


class OpenKlantServiceManager:
    _in_server_context: bool = False
    _django_service_name: str = "web"
    _api_root: str = "http://localhost:8338"
    _api_path: str = "/klantinteracties/api/v1"
    _api_token: str = "b2eb1da9861da88743d72a3fb4344288fe2cba44"
    _docker_compose_project_name: str = "openklant2-api-test"
    _docker_compose_path: Path = BASE_DIR / "docker-compose.yaml"

    def _docker_compose(
        self,
        *args: str,
        check: bool = True,
        input: str | None = None,
    ):
        input_data = {"text": True, "input": input} if input else {}
        try:
            return subprocess.run(
                args=[
                    "docker-compose",
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
                exc_info=True,
                extra={"stderr": exc.stderr, "stdout": exc.stdout},
            )
            raise

    def _manage_py(
        self,
        *args: str,
        input: str | None = None,
    ):
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
        self._manage_py(
            "loaddata",
            "--format",
            "json",
            "-",  # i.e. stdin
            input=fixture,
        )

    def _generate_token_fixture(self):
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
                # add admin user for convenience + debugging
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

    def _wait_for_response(self, interval=0.5, max_wait=60):
        start_time = time.time()
        while True:
            try:
                response = requests.get(self._api_root)
                return response
            except requests.RequestException:
                logger.debug("Exception while checking for liveness", exc_info=True)
                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait:
                    logger.info("Max wait time exceeded.")
                    raise RuntimeError(
                        f"Maximum wait for service to be healthy exceeded: {elapsed_time} > {max_wait}"
                    )

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

    @property
    def api_url(self):
        return urljoin(self._api_root, self._api_path)

    def client_factory(self):
        return OpenKlant2Client(
            base_url=self.api_url,
            request_kwargs={"headers": {"Authorization": f"Token {self._api_token}"}},
        )

    def clean_state(self):
        """Yield a client configured to talk a live OpenKlant service.

        Note that this requires the live server to have been spawned,
        either imperatively:

            service.setUp()
            with service.clean_state() as client:
                client.do_stuff()

            service.tearDown()

        ... or using the live_service() context manager:

            with service.live_server_manager() as live_service:
                with live_service.clean_state() as client:
                    client.do_something()

        """
        if not self._in_server_context:
            raise RuntimeError(
                "You must execute this context within the server context"
            )

        @contextmanager
        def clean_state_manager(*args, **kwds):
            self.reset_db_state()
            yield self.client_factory()

        return clean_state_manager()

    def live_service(self):
        """Context manager to spawn a live OpenKlant service and clean it up upon completion.

        You will commonly nest a clean_state() context manager within the live_service block,
        for instance:

            with service.live_server_manager() as live_service:
                with live_service.clean_state() as client:
                    client.do_something()
        """

        @contextmanager
        def live_server_manager(*args, **kwds):
            try:
                self.setUp()
                yield self
            finally:
                self.tearDown()

        return live_server_manager()


class LiveOpenKlantTestMixin:
    _service: OpenKlantServiceManager
    use_live_service: bool = False

    @classmethod
    def should_bypass_live_server(cls) -> bool:
        return cls.use_live_service

    @property
    def openklant_client(self) -> OpenKlant2Client:
        return self._service.client_factory()

    def reset_db(self):
        if not self.should_bypass_live_server():
            self._service.reset_db_state()

    @classmethod
    def setUpClass(cls):
        cls._service = OpenKlantServiceManager()

        if not cls.should_bypass_live_server():
            cls._service.setUp()

    @classmethod
    def tearDownClass(cls) -> None:
        if not cls.should_bypass_live_server():
            cls._service.tearDown()

    def setUp(self):
        self.reset_db()
