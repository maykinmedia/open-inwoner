from django.urls import include, path

from open_inwoner.urls import urlpatterns as root_urlpatterns

urlpatterns = [
    # add more here
    path("profile/", include("open_inwoner.cms.profile.urls")),
    path("cases/", include("open_inwoner.cms.cases.urls")),
] + root_urlpatterns
