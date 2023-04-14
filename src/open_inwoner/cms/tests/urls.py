from django.urls import include, path

from open_inwoner.urls import urlpatterns as root_urlpatterns

urlpatterns = [
    # add more here
    path("cases/", include("open_inwoner.cms.cases.urls")),
    path("profile/", include("open_inwoner.cms.profile.urls")),
    path("products/", include("open_inwoner.cms.products.urls")),
] + root_urlpatterns
