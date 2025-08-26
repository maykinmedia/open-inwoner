from django.urls import path

from .views.contactform import ContactFormView

app_name = "openklant"

# Note on Django CMS integration:
#
# The URL for a Django CMS page is determined by the page slug
# (e.g. "contactformulier"). CMS plugins construct their own path from
# page URL + the path from the application URL's. This will result in
# a URL like ".../contactformulier/contactformulier" for the contact form.
#
# For consistency with the URL naming pattern of the CMS flatpages, we leave
# the path empty so that the URL is determined solely by the CMS page slug

urlpatterns = [
    path("", ContactFormView.as_view(), name="contactform"),
]
