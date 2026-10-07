import json
import os
import socket
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from django_vite.core.asset_loader import DjangoViteConfig, ManifestEntry
from django_vite.core.exceptions import DjangoViteAssetNotFoundError

from open_inwoner.utils.vite import ReloadingManifestClient, ViteAppClient

ENTRY = "src/open_inwoner/react/main.ts"


class ReloadingManifestClientTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()

        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        self.manifest_path = Path(tmp_dir.name) / "manifest.json"

    def _write_manifest(self, file: str, mtime: int):
        self.manifest_path.write_text(
            json.dumps({ENTRY: {"file": file, "src": ENTRY, "isEntry": True}})
        )
        os.utime(self.manifest_path, ns=(mtime, mtime))

    def _client(self):
        return ReloadingManifestClient(
            DjangoViteConfig(manifest_path=self.manifest_path)
        )

    def test_reloads_changed_manifest(self):
        self._write_manifest("main.AbC123.js", mtime=1_000_000_000)
        client = self._client()

        self.assertEqual(
            client.get(ENTRY),
            ManifestEntry(file="main.AbC123.js", src=ENTRY, isEntry=True),
        )

        self._write_manifest("main.XyZ789.js", mtime=2_000_000_000)

        self.assertEqual(
            client.get(ENTRY),
            ManifestEntry(file="main.XyZ789.js", src=ENTRY, isEntry=True),
        )

    def test_picks_up_manifest_created_after_startup(self):
        client = self._client()

        with self.assertRaises(DjangoViteAssetNotFoundError):
            client.get(ENTRY)

        self._write_manifest("main.AbC123.js", mtime=1_000_000_000)

        self.assertEqual(
            client.get(ENTRY),
            ManifestEntry(file="main.AbC123.js", src=ENTRY, isEntry=True),
        )

    def test_keeps_previous_entries_for_unreadable_manifest(self):
        self._write_manifest("main.AbC123.js", mtime=1_000_000_000)
        client = self._client()

        self.manifest_path.write_text("{")
        os.utime(self.manifest_path, ns=(2_000_000_000, 2_000_000_000))

        self.assertEqual(
            client.get(ENTRY),
            ManifestEntry(file="main.AbC123.js", src=ENTRY, isEntry=True),
        )


class ViteAppClientDevModeTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()

        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        self.manifest_path = Path(tmp_dir.name) / "manifest.json"
        self.manifest_path.write_text(
            json.dumps({ENTRY: {"file": "main.AbC123.js", "src": ENTRY}})
        )

        self.server = socket.socket()
        self.server.bind(("localhost", 0))
        self.addCleanup(self.server.close)
        self.port = self.server.getsockname()[1]

    def _client(self, dev_mode=True):
        client = ViteAppClient(
            DjangoViteConfig(
                dev_mode=dev_mode,
                dev_server_port=self.port,
                static_url_prefix="bundles",
                manifest_path=self.manifest_path,
            )
        )
        # Probe on every lookup, rather than at most once a second
        client.DEV_SERVER_PROBE_INTERVAL = 0
        return client

    def test_serves_from_dev_server_while_port_is_open(self):
        self.server.listen()
        client = self._client()

        self.assertTrue(client.dev_mode)
        self.assertEqual(
            client.generate_vite_asset_url(ENTRY),
            f"http://localhost:{self.port}/static/bundles/{ENTRY}",
        )

    def test_falls_back_to_manifest_while_port_is_closed(self):
        client = self._client()

        self.assertFalse(client.dev_mode)
        self.assertEqual(
            client.generate_vite_asset_url(ENTRY), "/static/bundles/main.AbC123.js"
        )

    def test_detects_dev_server_started_after_startup(self):
        client = self._client()
        self.assertFalse(client.dev_mode)

        self.server.listen()

        self.assertTrue(client.dev_mode)

    def test_never_uses_dev_server_with_dev_mode_disabled(self):
        self.server.listen()
        client = self._client(dev_mode=False)

        self.assertFalse(client.dev_mode)

    def test_caches_probe_result(self):
        client = self._client()
        client.DEV_SERVER_PROBE_INTERVAL = 60
        self.assertFalse(client.dev_mode)

        self.server.listen()

        self.assertFalse(client.dev_mode)
