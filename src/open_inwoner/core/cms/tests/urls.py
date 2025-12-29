from django.urls import include, path

from open_inwoner.urls import urlpatterns as root_urlpatterns

urlpatterns = [
    path("cases/", include("open_inwoner.mijn_aanvragen.urls")),
    path("profile/", include("open_inwoner.accounts.cms.mijn_profiel.urls")),
    path("products/", include("open_inwoner.onderwerpen.cms.urls")),
    path("inbox/", include("open_inwoner.accounts.cms.mijn_berichten.urls")),
    path("collaborate/", include("open_inwoner.mijn_samenwerkingen.cms.urls")),
    path("uitkeringen/", include("open_inwoner.mijn_uitkeringen.urls")),
    path("openklant/", include("open_inwoner.openklant.urls")),
] + root_urlpatterns
