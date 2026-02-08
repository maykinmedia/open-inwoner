from open_inwoner.cms.utils import get_published_pages_with_apphooks


def active_apphooks(request):
    """
    add lookup of active CMS apps to context

    "cms_apps": {
        "ProfileApphook": True,
        "profile": True,
    }
    """
    active_app_hooks = get_published_pages_with_apphooks().values_list(
        "application_urls", "application_namespace"
    )

    lookup = dict()

    for classname, namespace in active_app_hooks:
        lookup[classname] = True
        lookup[namespace] = True

    context = {"cms_apps": lookup}
    return context
