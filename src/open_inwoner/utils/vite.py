import math
import socket
import time

from django_vite.core.asset_loader import (
    DEFAULT_APP_NAME,
    DjangoViteAppClient,
    DjangoViteConfig,
    ManifestClient,
)
from django_vite.core.exceptions import DjangoViteManifestError


class ReloadingManifestClient(ManifestClient):
    """
    Manifest client that re-reads ``manifest.json`` whenever it changes.

    django-vite parses the manifest once per process, but every frontend build
    replaces the content-hashed bundles (and removes the old ones), so without
    this Django would have to be restarted after each ``npm run build``.

    The manifest is loaded even with ``dev_mode`` enabled, because it is the
    fallback whenever the Vite dev server is not running (see ``ViteAppClient``).
    """

    def __init__(
        self, config: DjangoViteConfig, app_name: str = DEFAULT_APP_NAME
    ) -> None:
        super().__init__(config._replace(dev_mode=False), app_name)
        self._entries_mtime = self._get_manifest_mtime()

    def _get_manifest_mtime(self) -> int | None:
        try:
            return self.manifest_path.stat().st_mtime_ns
        except FileNotFoundError:
            return None

    def get(self, path):
        mtime = self._get_manifest_mtime()
        if mtime != self._entries_mtime:
            try:
                self._entries, self.legacy_polyfills_entry = self._parse_manifest()
            except DjangoViteManifestError:
                # Possibly caught halfway through a build: keep the previous
                # entries and retry on the next lookup.
                pass
            else:
                self._entries_mtime = mtime
        return super().get(path)


class ViteAppClient(DjangoViteAppClient):
    """
    App client that only serves assets from the Vite dev server while it runs.

    With ``dev_mode`` enabled, the dev server's port is probed (at most once per
    ``DEV_SERVER_PROBE_INTERVAL`` seconds): assets come from the dev server while
    ``npm run watch`` is listening, and from the build output otherwise.
    """

    ManifestClient = ReloadingManifestClient

    DEV_SERVER_PROBE_INTERVAL = 1.0
    DEV_SERVER_PROBE_TIMEOUT = 0.1

    _dev_server_probed_at = -math.inf
    _dev_server_running = False

    @property
    def dev_mode(self) -> bool:
        return self._dev_mode_enabled and self._is_dev_server_running()

    @dev_mode.setter
    def dev_mode(self, value: bool) -> None:
        self._dev_mode_enabled = value

    def _is_dev_server_running(self) -> bool:
        now = time.monotonic()
        if now - self._dev_server_probed_at >= self.DEV_SERVER_PROBE_INTERVAL:
            self._dev_server_running = self._probe_dev_server()
            self._dev_server_probed_at = now
        return self._dev_server_running

    def _probe_dev_server(self) -> bool:
        try:
            with socket.create_connection(
                (self.dev_server_host, self.dev_server_port),
                timeout=self.DEV_SERVER_PROBE_TIMEOUT,
            ):
                return True
        except OSError:
            return False
