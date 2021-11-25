from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic.base import TemplateView

from open_inwoner.accounts.views import DocumentPrivateMediaView, PasswordResetView

handler500 = "open_inwoner.utils.views.server_error"
admin.site.site_header = "Open Inwoner beheeromgeving"
admin.site.site_title = "Open Inwoner beheeromgeving"
admin.site.index_title = "Welkom op de OpenInwoner beheeromgeving"


urlpatterns = [
    path(
        "admin/password_reset/",
        PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "private_files/<path>",
        DocumentPrivateMediaView.as_view(),
        name="private_file",
    ),
    path("admin/hijack/", include("hijack.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("open_inwoner.api.urls", namespace="api")),
    path("ckeditor/", include("open_inwoner.ckeditor.urls")),
    # Simply show the master template.
    path("", TemplateView.as_view(template_name="master.html"), name="root"),
]

# NOTE: The staticfiles_urlpatterns also discovers static files (ie. no need to run collectstatic). Both the static
# folder and the media folder are only served via Django if DEBUG = True.
urlpatterns += staticfiles_urlpatterns() + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if "digid_eherkenning.backends.DigiDBackend" in settings.AUTHENTICATION_BACKENDS:
    urlpatterns = [
        path("digid/", include("digid_eherkenning.digid_urls")),
    ] + urlpatterns
else:
    urlpatterns = [
        path("digid/", include("digid_eherkenning.mock.digid_urls")),
        path("digid/idp/", include("digid_eherkenning.mock.idp.digid_urls")),
    ] + urlpatterns

if settings.DEBUG and apps.is_installed("debug_toolbar"):
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
