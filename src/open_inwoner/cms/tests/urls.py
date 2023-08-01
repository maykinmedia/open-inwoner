from django.urls import include, path

from open_inwoner.urls import urlpatterns as root_urlpatterns

urlpatterns = [
    path("cases/", include("open_inwoner.cms.cases.urls")),
    path("profile/", include("open_inwoner.cms.profile.urls")),
    path("products/", include("open_inwoner.cms.products.urls")),
    path("inbox/", include("open_inwoner.cms.inbox.urls")),
    path("collaborate/", include("open_inwoner.cms.collaborate.urls")),
    path("uitkeringen/", include("open_inwoner.cms.ssd.urls")),
] + root_urlpatterns
