import tempfile
from pathlib import Path

from django.core.management import call_command
from django.templatetags.static import static
from django.test import SimpleTestCase, override_settings


class ViteManifestStaticFilesStorageTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()

        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        source_dir = Path(tmp_dir.name) / "source"
        self.static_root = Path(tmp_dir.name) / "root"

        bundles_dir = source_dir / "bundles"
        bundles_dir.mkdir(parents=True)
        (source_dir / "img").mkdir()
        (source_dir / "img" / "logo.png").write_bytes(b"png")
        (bundles_dir / "open_inwoner-frontend.AbC123.js").write_text(
            'export const h=1;import("./SideNav.QqQ.bundle.js");\n'
        )
        (bundles_dir / "SideNav.QqQ.bundle.js").write_text(
            'import{h}from"./open_inwoner-frontend.AbC123.js";\n'
        )
        (bundles_dir / "open_inwoner-frontend.XyZ789.css").write_text(
            ".a{background:url(../img/logo.png)}\n"
        )

        settings = override_settings(
            STATIC_ROOT=str(self.static_root),
            STATICFILES_DIRS=[str(source_dir)],
            STORAGES={
                "staticfiles": {
                    "BACKEND": "open_inwoner.utils.files.ViteManifestStaticFilesStorage"
                }
            },
        )
        settings.enable()
        self.addCleanup(settings.disable)

    def test_does_not_rehash_vite_bundles(self):
        call_command("collectstatic", interactive=False, verbosity=0)

        logo_url = static("img/logo.png")
        self.assertRegex(logo_url, r"^/static/img/logo\.[0-9a-f]{12}\.png$")
        self.assertEqual(
            [
                static("bundles/open_inwoner-frontend.AbC123.js"),
                static("bundles/SideNav.QqQ.bundle.js"),
            ],
            [
                "/static/bundles/open_inwoner-frontend.AbC123.js",
                "/static/bundles/SideNav.QqQ.bundle.js",
            ],
        )
        self.assertEqual(
            sorted(path.name for path in (self.static_root / "bundles").iterdir()),
            [
                "SideNav.QqQ.bundle.js",
                "open_inwoner-frontend.AbC123.js",
                "open_inwoner-frontend.XyZ789.css",
            ],
        )
        # References from bundles to non-bundled files are still rewritten
        self.assertEqual(
            (
                self.static_root / "bundles" / "open_inwoner-frontend.XyZ789.css"
            ).read_text(),
            '.a{background:url("%s")}\n' % logo_url.replace("/static/", "../"),
        )
