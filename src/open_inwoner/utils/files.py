from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    """Custom upload file storage for overwriting files with the same name"""

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name


# Static asset references that are known to be broken in a vendored/third-party
# package, and that we deliberately let ManifestStaticFilesStorage leave
# unhashed instead of hard-failing collectstatic. Keep this list narrow: any
# other missing reference should still fail the build loudly, exactly as
# ManifestStaticFilesStorage intends.
KNOWN_MISSING_STATIC_REFERENCES = {
    # maykin-django-prosemirror==0.9.0 ships a minified bundle with a dangling
    # `//# sourceMappingURL=bundle.js.map` comment, but the .map file itself
    # isn't included in the wheel. Remove this entry once that's fixed
    # upstream: https://github.com/maykinmedia/django-prosemirror
    "js/bundle.js.map",
}


class TolerantManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    ManifestStaticFilesStorage that doesn't fail collectstatic over specific,
    known-broken references to missing static files (see
    ``KNOWN_MISSING_STATIC_REFERENCES``). Every other missing reference still
    raises, same as the base class.
    """

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except ValueError:
            if self.clean_name(name) in KNOWN_MISSING_STATIC_REFERENCES:
                return name
            raise


# Directory with the Vite build output, which Vite content-hashes by itself.
VITE_BUNDLES_DIR = "bundles/"


class ViteManifestStaticFilesStorage(TolerantManifestStaticFilesStorage):
    """
    Manifest storage that leaves the (already content-hashed) Vite bundles
    unhashed.

    The bundles import each other by their Vite file names, which Django can't
    rewrite in the files Vite's runtime loads. Serving a Django-hashed copy of
    an entry next to those would make the browser evaluate it twice, as two
    separate modules (e.g. two preact instances).
    """

    def hashed_name(self, name, content=None, filename=None):
        if self.clean_name(name).startswith(VITE_BUNDLES_DIR):
            return name
        return super().hashed_name(name, content, filename)
