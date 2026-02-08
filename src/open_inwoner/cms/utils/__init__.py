"""
CMS utilities for Django CMS 4.x with djangocms-versioning.

These helpers abstract the versioning checks needed to determine if pages
and their content are published.
"""

from django.contrib.sites.models import Site
from django.db.models import Q, QuerySet

from cms.models import Page, PageContent
from djangocms_versioning.constants import PUBLISHED
from djangocms_versioning.models import Version


def get_published_page_ids() -> QuerySet:
    """
    Get a queryset of page IDs that have published PageContent.

    This is the core helper that other functions build upon.

    Returns:
        QuerySet of page IDs (integers) that have published content.
    """
    published_page_content_ids = Version.objects.filter(
        state=PUBLISHED,
        content_type__model="pagecontent",
    ).values_list("object_id", flat=True)

    return PageContent.objects.filter(id__in=published_page_content_ids).values_list(
        "page_id", flat=True
    )


def get_published_pages(site: Site | None = None) -> QuerySet[Page]:
    """
    Get a queryset of pages that have published content.

    Args:
        site: Optional site to filter pages for. If None, uses the current site.

    Returns:
        QuerySet of Page objects that have at least one published PageContent.
    """
    if site is None:
        site = Site.objects.get_current()

    published_page_ids = get_published_page_ids()

    return Page.objects.filter(
        pk__in=published_page_ids,
        node__site=site,
    )


def is_page_published(page: Page, language: str | None = None) -> bool:
    """
    Check if a specific page has published content.

    Args:
        page: The Page object to check.
        language: Optional language code. If provided, checks for published
                  content in that specific language.

    Returns:
        True if the page has published content, False otherwise.
    """
    from django.conf import settings

    if language is None:
        language = settings.LANGUAGE_CODE

    page_content = PageContent.objects.filter(page=page, language=language).first()
    if not page_content:
        return False

    try:
        version = Version.objects.get_for_content(page_content)
        return version.state == PUBLISHED
    except Version.DoesNotExist:
        return False


def get_published_pages_with_apphooks() -> QuerySet[Page]:
    """
    Get pages that have an apphook configured AND are published.

    Returns:
        QuerySet of Page objects with apphooks that have published content.
    """
    pages_with_apphooks = Page.objects.exclude(
        Q(application_urls="") | Q(application_urls__isnull=True)
    )

    published_page_ids = get_published_page_ids()

    return pages_with_apphooks.filter(id__in=published_page_ids)


def has_published_apphook(apphook_class_or_name: type | str) -> bool:
    """
    Check if a page with a specific apphook is published.

    Args:
        apphook_class_or_name: Either the apphook class or its class name string.

    Returns:
        True if a page with this apphook exists and is published.
    """
    if isinstance(apphook_class_or_name, str):
        apphook_name = apphook_class_or_name
    else:
        apphook_name = apphook_class_or_name.__name__

    pages_with_apphook = Page.objects.filter(application_urls=apphook_name)
    if not pages_with_apphook.exists():
        return False

    published_page_ids = get_published_page_ids()
    return pages_with_apphook.filter(id__in=published_page_ids).exists()


def get_page_content(
    page: Page, language: str | None = None, include_drafts: bool = False
) -> PageContent | None:
    """
    Get the PageContent for a page in a specific language.

    In CMS 4.x, PageContent stores the title, template, and placeholders
    for each language version of a page.

    Args:
        page: The Page object.
        language: Language code. If None, uses the default language.
        include_drafts: If True, falls back to admin_manager to include
                        draft content if no published content is found.

    Returns:
        PageContent object or None if not found.
    """
    from django.conf import settings

    if language is None:
        language = settings.LANGUAGE_CODE

    # Try published content first
    page_content = PageContent.objects.filter(page=page, language=language).first()

    # Fall back to drafts if requested and no published content found
    if not page_content and include_drafts:
        page_content = PageContent.admin_manager.filter(
            page=page, language=language
        ).first()

    return page_content


def get_page_placeholders(
    page: Page, language: str | None = None, include_drafts: bool = False
) -> QuerySet:
    """
    Get all placeholders for a page.

    In CMS 4.x, placeholders are on PageContent, not directly on Page.

    Args:
        page: The Page object.
        language: Language code. If None, uses the default language.
        include_drafts: If True, includes draft content when looking for placeholders.

    Returns:
        QuerySet of Placeholder objects, or empty queryset if no PageContent found.
    """
    from cms.models import Placeholder

    page_content = get_page_content(page, language, include_drafts)
    if not page_content:
        return Placeholder.objects.none()

    return page_content.placeholders.all()


def get_page_placeholder(
    page: Page,
    slot: str,
    language: str | None = None,
    include_drafts: bool = False,
):
    """
    Get a specific placeholder by slot name for a page.

    In CMS 4.x, placeholders are on PageContent, not directly on Page.

    Args:
        page: The Page object.
        slot: The placeholder slot name (e.g., "content").
        language: Language code. If None, uses the default language.
        include_drafts: If True, includes draft content when looking for placeholders.

    Returns:
        Placeholder object or None if not found.
    """
    page_content = get_page_content(page, language, include_drafts)
    if not page_content:
        return None

    try:
        return page_content.placeholders.get(slot=slot)
    except page_content.placeholders.model.DoesNotExist:
        return None
