from django.urls import path

from .views import DownloadExportView

app_name = "private_files"
urlpatterns = [
    path("<path>/", DownloadExportView.as_view(), name="private_file"),
]
