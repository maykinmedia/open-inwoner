from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.functional import LazyObject


class PrivateFileSystemStorage(FileSystemStorage):
    """
    Storage that puts files in the private media folder that isn't
    globally available.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", settings.PRIVATE_MEDIA_ROOT)
        kwargs.setdefault("base_url", settings.PRIVATE_MEDIA_URL)
        super().__init__(*args, **kwargs)


class PrivateStorage(LazyObject):
    def _setup(self):
        self._wrapped = PrivateFileSystemStorage()


private_storage = PrivateStorage()
