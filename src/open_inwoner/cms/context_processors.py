from django.db.models import Q
from django.utils.functional import SimpleLazyObject

from cms.models import Page

from open_inwoner.cms.utils.page_display import get_published_page_ids
from open_inwoner.components.templatetags.menu import get_sidenav_items


def active_apphooks(request):
    """
    add lookup of active CMS apps to context

    "cms_apps": {
        "ProfileApphook": True,
        "profile": True,
    }
    """
    active_app_hooks = (
        Page.objects.filter(id__in=get_published_page_ids())
        .exclude(Q(application_urls="") | Q(application_urls__isnull=True))
        .values_list("application_urls", "application_namespace")
    )

    lookup = dict()

    for classname, namespace in active_app_hooks:
        lookup[classname] = True
        lookup[namespace] = True

    context = {"cms_apps": lookup}
    return context


def sidenav(request):
    """
    add the side navigation menu items to the context

    Lazy on purpose: building the items walks the CMS menu tree and queries per
    node, which should not happen on requests that never render the sidenav,
    such as the admin.
    """
    return {"sidenav_items": SimpleLazyObject(lambda: get_sidenav_items(request))}
