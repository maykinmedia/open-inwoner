from django.urls import path

from .views import DownloadExportView


urlpatterns = [
    path("private_files/<path>", DownloadExportView.as_view(), name="private_file"),
]
