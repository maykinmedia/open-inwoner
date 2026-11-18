from django.contrib import admin
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase


def _relative_static_paths(media):
    paths = [*media._js, *(p for ps in media._css.values() for p in ps)]
    for path in paths:
        path = getattr(path, "path", path)
        if "://" in path or path.startswith("/"):
            continue
        yield path


class AdminMediaStaticFilesTests(SimpleTestCase):
    def test_admin_media_static_files_exist(self):
        # A missing file breaks the admin page under the strict manifest storage
        missing = {
            f"{model._meta.label}: {path}"
            for model, model_admin in admin.site._registry.items()
            for path in _relative_static_paths(model_admin.media)
            if finders.find(path) is None
        }

        self.assertEqual(missing, set())
