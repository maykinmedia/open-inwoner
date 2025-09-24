from django.urls import include, path
from django.views.generic import TemplateView

# Profile URLs (needed for exclude_urls_from_menu check)
profile_patterns = [
    path("detail/", TemplateView.as_view(), name="detail"),
]

# Minimal URL configuration for CMS tests
urlpatterns = [
    # Add profile namespace to prevent NoReverseMatch in exclude_urls_from_menu
    path("profile/", include((profile_patterns, "profile"), namespace="profile")),
    # Add FAQ URL for extra menu items
    path("faq/", TemplateView.as_view(), name="general_faq"),
    # CMS URLs (must be last to catch all remaining patterns)
    path("", include("cms.urls")),
]
