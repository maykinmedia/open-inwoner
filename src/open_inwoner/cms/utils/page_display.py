"""Utilities for determining whether CMS pages are published"""


from django.db.models import Q

from cms.models import Page

from open_inwoner.cms.benefits.cms_apps import SSDApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.inbox.cms_apps import InboxApphook

cms_apps = {
    "inbox": InboxApphook,
    "collaborate": CollaborateApphook,
    "cases": CasesApphook,
    "ssd": SSDApphook,
}


def _is_published(page_name: str) -> bool:
    """
    Determine whether the page associated with a specific CMS app is published
    """
    page = Page.objects.filter(
        application_namespace=cms_apps[page_name].app_name, publisher_is_draft=False
    ).first()
    return page and page.is_published(page.languages)


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


def get_active_app_names() -> list[str]:
    return list(
        Page.objects.published()
        .exclude(
            Q(application_urls="")
            | Q(application_urls__isnull=True)
            | Q(application_namespace="")
        )
        .values_list("application_namespace", flat=True)
    )
