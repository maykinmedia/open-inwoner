from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

import structlog
from cms.models import Page, Title

from open_inwoner.accounts.models import User
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.utils.page_display import (
    benefits_page_is_published,
    case_page_is_published,
    collaborate_page_is_published,
    inbox_page_is_published,
    products_page_is_published,
    profile_page_is_published,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import KlantenSysteemConfig
from open_inwoner.pdc.models.category import Category
from open_inwoner.questionnaire.models import QuestionnaireStep

logger = structlog.stdlib.get_logger(__name__)


def _get_category_data_for_user(cat: Category, user: User) -> dict:
    return {
        "category": cat,
        "sub_categories": [
            _get_category_data_for_user(child, user)
            for child in cat.get_children()
            .filter(published=True)
            .visible_for_user(user)
        ],
        "products": cat.products.filter(published=True),
    }


def _get_profile_config():
    """
    Get ProfileConfig instance, handling DoesNotExist and MultipleObjectsReturned
    """
    try:
        return ProfileConfig.objects.get()
    except ProfileConfig.DoesNotExist:
        return None
    except ProfileConfig.MultipleObjectsReturned:
        logger.warning("Multiple instances of ProfileConfig apphook found")
        return ProfileConfig.objects.first()


def _get_app_pages() -> list[dict]:
    """
    Get app-specific pages (benefits, cases, collaborate, inbox).

    Returns a list of page dictionaries with app page links for authenticated
    users only.
    """
    pages = []

    if benefits_page_is_published():
        pages.append(
            {"url_name": "ssd:uitkeringen", "link_text": _("Mijn uitkeringen")}
        )
    if case_page_is_published():
        pages.append({"url_name": "cases:index", "link_text": _("Mijn zaken")})
        pages.append(
            {"url_name": "cases:contactmoment_list", "link_text": _("Mijn vragen")}
        )
    if collaborate_page_is_published():
        pages.append(
            {"url_name": "collaborate:plan_list", "link_text": _("Mijn samenwerkingen")}
        )
    if inbox_page_is_published():
        pages.append({"url_name": "inbox:index", "link_text": _("Mijn berichten")})

    return pages


def _get_questionnaire_page(profile_config) -> list:
    """
    Get questionnaire page (Zelftest or Zelfdiagnose variant).

    Returns a list with zero or one page dictionary.
    """
    # "Zelfdiagnose": enabled when selfdiagnose flag is on and questionnaires exist
    # "Zelftest": shown when products page is published (regardless of questionnaires)
    if (
        profile_config
        and profile_config.selfdiagnose
        and QuestionnaireStep.objects.filter(published=True).exists()
    ):
        return [
            {"url_name": "products:questionnaire_list", "link_text": _("Zelfdiagnose")}
        ]
    elif products_page_is_published():
        return [{"url_name": "products:questionnaire_list", "link_text": _("Zelftest")}]
    return []


def _get_profile_section_pages(profile_config) -> list:
    """
    Get profile section pages based on ProfileConfig toggles.

    Returns a list of page dictionaries for profile subsections.
    """
    pages = []

    if profile_config.selected_categories:
        pages.append(
            {"url_name": "profile:categories", "link_text": _("Mijn Interessegebieden")}
        )
    if profile_config.mentors:
        base_url = reverse("profile:contact_list")
        begeleiders_url = f"{base_url}?{urlencode({'type': 'begeleider'})}"
        pages.append({"url": begeleiders_url, "link_text": _("Mijn begeleiders")})
    if profile_config.my_contacts:
        pages.append(
            {"url_name": "profile:contact_list", "link_text": _("Mijn contacten")}
        )
    if profile_config.actions:
        pages.append(
            {"url_name": "profile:action_list", "link_text": _("Openstaande acties")}
        )
    if profile_config.notifications:
        pages.append(
            {
                "url_name": "profile:notifications",
                "link_text": _("Notificatievoorkeuren"),
            }
        )
    if profile_config.appointments:
        pages.append(
            {"url_name": "profile:appointments", "link_text": _("Mijn afspraken")}
        )

    return pages


def _get_footer_pages(is_authenticated: bool) -> list:
    """
    Get footer CMS pages from site configuration.

    Returns a list of page dictionaries, filtered by authentication if needed.
    """
    config = SiteConfiguration.get_solo()
    klant_config = KlantenSysteemConfig.get_solo()
    cms_footer_pages = list(config.get_ordered_cms_pages())

    # Add contact form page at the beginning if enabled
    contact_form_pages = Page.objects.filter(
        template="cms/contactform/form_outer.html", publisher_is_draft=False
    )
    if contact_form_pages.exists() and klant_config.contact_registration_enabled:
        cms_footer_pages.insert(0, contact_form_pages.first())

    # Filter out auth-required pages for anonymous users
    if not is_authenticated:
        cms_footer_pages = [
            page
            for page in cms_footer_pages
            if not hasattr(page, "commonextension")
            or not page.commonextension.requires_auth
        ]

    pages = []
    for page in cms_footer_pages:
        title = Title.objects.get(page=page, language=page.languages)
        pages.append({"url": page.get_absolute_url(), "link_text": title.title})

    return pages


def _get_sitemap_pages(request) -> list:
    """
    Get all sitemap pages in a flat list, sorted alphabetically.

    Pages are filtered based on:
    - User authentication status
    - CMS page publication status
    - ProfileConfig toggles

    Returns a list of page dictionaries with 'url' or 'url_name' and 'link_text'.
    """
    is_authenticated = request.user.is_authenticated
    profile_config = _get_profile_config()

    pages = []

    # Home page (always visible)
    pages.append({"url_name": "pages-root", "link_text": _("Home page")})

    # Sitemap (always visible)
    pages.append({"url_name": "sitemap", "link_text": _("Sitemap")})

    # Questionnaire page (Zelftest or Zelfdiagnose)
    pages.extend(_get_questionnaire_page(profile_config))

    # Footer pages (some visible for anon users)
    pages.extend(_get_footer_pages(is_authenticated))

    if is_authenticated:
        # App pages (benefits, cases, collaborate, inbox)
        pages.extend(_get_app_pages())

        # Profile pages
        if profile_page_is_published() and profile_config:
            pages.append({"url_name": "profile:detail", "link_text": _("Mijn profiel")})
            pages.extend(_get_profile_section_pages(profile_config))
    else:
        # Login link (only for anonymous users)
        pages.append(
            {"url_name": "login", "link_text": _("Login or create an account")}
        )

    # Sort alphabetically by link text
    pages.sort(key=lambda p: str(p["link_text"]))

    return pages


def sitemap(request):
    """
    Collect internal links for display in sitemap page
    """
    template_name = "pages/sitemap/sitemap.html"

    # Add onderwerpen/categories
    root_categories = (
        Category.get_root_nodes().published().visible_for_user(request.user)
    )
    context = {
        "category_nodes": [
            _get_category_data_for_user(category, request.user)
            for category in root_categories
        ],
        "sitemap_pages": _get_sitemap_pages(request),
    }

    return render(request, template_name, context)
