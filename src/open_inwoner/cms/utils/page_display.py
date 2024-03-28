"""Utilities for determining whether CMS pages are published"""


from django.db.models import Q

from cms.models import Page

from open_inwoner.cms.benefits.cms_apps import SSDApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.inbox.cms_apps import InboxApphook
from open_inwoner.cms.profile.cms_apps import ProfileApphook

cms_apps = {
    hook.app_name: hook
    for hook in [
        InboxApphook,
        CollaborateApphook,
        CasesApphook,
        SSDApphook,
        ProfileApphook,
    ]
}


def _is_published(page_name: str) -> bool:
    """
    Determine whether the page associated with a specific CMS app is published
    """
    hook = cms_apps.get(page_name)
    if not hook:
        return False
    # CMS uses the hook's classname as urls value
    # NOTE: the old approach of filtering on application_namespace breaks for hooks with app-configs
    page = Page.objects.filter(
        application_urls=hook.__name__, publisher_is_draft=False
    ).first()
    return bool(page and page.is_published(page.languages))


def inbox_page_is_published() -> bool:
    """
    :returns: True if the inbox/message page is published, False otherwise
    """
    return _is_published("inbox")


def case_page_is_published() -> bool:
    """
    :returns: True if the case page is published, False otherwise
    """
    return _is_published("cases")


def collaborate_page_is_published() -> bool:
    """
    :returns: True if the collaborate page published, False otherwise
    """
    return _is_published("collaborate")


def benefits_page_is_published() -> bool:
    """
    :returns: True if the social benefits page published, False otherwise
    """
    return _is_published("ssd")


def profile_page_is_published() -> bool:
    """
    :returns: True if the profile page published, False otherwise
    """
    return _is_published("profile")


def get_active_app_names() -> list[str]:
    qs = (
        Page.objects.published()
        .exclude(
            Q(application_urls="")
            | Q(application_urls__isnull=True)
            | Q(application_namespace="")
        )
        .values_list("application_urls", flat=True)
    )
    # CMS uses the hook's classname as urls value
    # NOTE: the old approach of filtering on application_namespace breaks for hooks with app-configs

    hook_lookup = {hook.__name__: name for name, hook in cms_apps.items()}
    names = set()
    for value in qs:
        if name := hook_lookup.get(value):
            names.add(name)
    return list(names)
