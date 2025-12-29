from django.urls import path

from .views.zaken_plugin import zaken_plugin_content_view

app_name = "cms_plugins"

urlpatterns = [
    path(
        "zaken/<int:plugin_id>/content/",
        zaken_plugin_content_view,
        name="zaken_content",
    ),
]
