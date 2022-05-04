from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from open_inwoner.accounts.forms import CustomRegistrationForm
from open_inwoner.accounts.views import CustomRegistrationView, PasswordResetView
from open_inwoner.pdc.views import FAQView, HomeView

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
    path("admin/hijack/", include("hijack.urls")),
    path("admin/", admin.site.urls),
    path("ckeditor/", include("open_inwoner.ckeditor5.urls")),
    # Simply show the master template.
    path(
        "accounts/register/",
        CustomRegistrationView.as_view(form_class=CustomRegistrationForm),
        name="django_registration_register",
    ),
    path("accounts/", include("django_registration.backends.one_step.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include("open_inwoner.api.urls", namespace="api")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # Views
    path("accounts/", include("open_inwoner.accounts.urls", namespace="accounts")),
    path("pages/", include("django.contrib.flatpages.urls"), name="flatpages"),
    path("mail-editor/", include("mail_editor.urls", namespace="mail_editor")),
    path("plans/", include("open_inwoner.plans.urls", namespace="plans")),
    path(
        "questionnaire/",
        include("open_inwoner.questionnaire.urls", namespace="questionnaire"),
    ),
    path("sessions/", include("extended_admin_session.urls", namespace="extended")),
    path("faq/", FAQView.as_view(), name="general_faq"),
    path("", include("open_inwoner.pdc.urls", namespace="pdc")),
    path("", include("open_inwoner.search.urls", namespace="search")),
    path("", HomeView.as_view(), name="root"),
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
