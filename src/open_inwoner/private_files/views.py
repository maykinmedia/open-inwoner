from django.core.exceptions import PermissionDenied
from django.views import View

from sendfile import sendfile

from .storage import private_storage


class DownloadExportView(View):
    def get(self, request, path):
        if request.user.is_authenticated:
            fs_path = private_storage.path(path)
            return sendfile(request, fs_path, attachment=True)

        raise PermissionDenied
