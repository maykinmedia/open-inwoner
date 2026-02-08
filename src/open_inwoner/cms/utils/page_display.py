"""Utilities for determining whether CMS pages are published"""

from cms.models import Page

from open_inwoner.cms.benefits.cms_apps import SSDApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.inbox.cms_apps import InboxApphook
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.utils import (
    get_published_pages_with_apphooks,
    is_page_published,
)

cms_apps = {
    hook.app_name: hook
    for hook in [
        InboxApphook,
        CollaborateApphook,
        CasesApphook,
        SSDApphook,
        ProductsApphook,
        ProfileApphook,
    ]
}


def _is_published(page_name: str) -> bool:
    """
    Determine whether the page associated with a specific CMS app is published.

    In CMS 4.x with djangocms-versioning, we check if the page has a published
    PageContent version.
    """
    hook = cms_apps.get(page_name)
    if not hook:
        return False
    # CMS uses the hook's classname as urls value
    # NOTE: the old approach of filtering on application_namespace breaks for hooks with app-configs
    page = Page.objects.filter(application_urls=hook.__name__).first()
    if not page:
        return False

    return is_page_published(page)


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


def products_page_is_published() -> bool:
    """
    :returns: True if the product page published, False otherwise
    """
    return _is_published("products")


def profile_page_is_published() -> bool:
    """
    :returns: True if the profile page published, False otherwise
    """
    return _is_published("profile")


def get_active_app_names() -> list[str]:
    qs = (
        get_published_pages_with_apphooks()
        .exclude(application_namespace="")
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
