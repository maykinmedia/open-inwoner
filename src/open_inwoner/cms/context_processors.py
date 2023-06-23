from django.db.models import Q

from cms.models import Page


def active_apphooks(request):
    """
    add lookup of active CMS apps to context

    "cms_apps": {
        "ProfileApphook": True,
        "profile": True,
    }
    """
    active_app_hooks = (
        Page.objects.published()
        .exclude(Q(application_urls="") | Q(application_urls__isnull=True))
        .values_list("application_urls", "application_namespace")
    )

    lookup = dict()

    for classname, namespace in active_app_hooks:
        lookup[classname] = True
        lookup[namespace] = True

    context = {"cms_apps": lookup}
    return context
