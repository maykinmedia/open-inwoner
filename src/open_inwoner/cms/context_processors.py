from django.db.models import Q

from cms.models import Page, PageContent
from djangocms_versioning.constants import PUBLISHED


def active_apphooks(request):
    """
    add lookup of active CMS apps to context

    "cms_apps": {
        "ProfileApphook": True,
        "profile": True,
    }
    """
    published_page_ids = PageContent._original_manager.filter(
        versions__state=PUBLISHED
    ).values_list("page_id", flat=True)
    active_app_hooks = (
        Page.objects.filter(id__in=published_page_ids)
        .exclude(Q(application_urls="") | Q(application_urls__isnull=True))
        .values_list("application_urls", "application_namespace")
    )

    lookup = dict()

    for classname, namespace in active_app_hooks:
        lookup[classname] = True
        lookup[namespace] = True

    context = {"cms_apps": lookup}
    return context
