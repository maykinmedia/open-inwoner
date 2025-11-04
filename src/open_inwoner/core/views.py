import logging
from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

from cms.models import Title

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

logger = logging.getLogger(__name__)


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


def _get_cms_pages() -> list:
    """
    Get app-specific CMS pages for the sitemap

    Returns a list of app-specific page dictionaries (Mijn uitkeringen, Mijn zaken, etc.)
    """
    cms_pages = []

    if benefits_page_is_published():
        cms_pages.append(
            {"url_name": "ssd:uitkeringen", "link_text": _("Mijn uitkeringen")}
        )
    if case_page_is_published():
        cms_pages.append({"url_name": "cases:index", "link_text": _("Mijn zaken")})
        cms_pages.append(
            {"url_name": "cases:contactmoment_list", "link_text": _("Mijn vragen")}
        )
    if collaborate_page_is_published():
        cms_pages.append(
            {"url_name": "collaborate:plan_list", "link_text": _("Mijn samenwerkingen")}
        )
    if inbox_page_is_published():
        cms_pages.append({"url_name": "inbox:index", "link_text": _("Mijn berichten")})
    if products_page_is_published():
        cms_pages.append(
            {"url_name": "products:questionnaire_list", "link_text": _("Zelftest")}
        )

    return cms_pages


def _get_cms_profile_pages() -> list:
    """
    Get profile-related CMS pages for the sitemap

    Returns a list of profile page dictionaries (Mijn profiel, Mijn contacten, etc.)
    """
    if not profile_page_is_published():
        return []

    cms_profile_pages = [
        {"url_name": "profile:detail", "link_text": _("Mijn profiel")},
    ]

    # Conditionally add cms pages based on apphook configuration
    try:
        profile_config = ProfileConfig.objects.get()
    except ProfileConfig.MultipleObjectsReturned:
        logger.warning("Multiple instances of ProfileConfig apphook found")
        profile_config = ProfileConfig.objects.first()

    if profile_config.selected_categories:
        cms_profile_pages.append(
            {
                "url_name": "profile:categories",
                "link_text": _("Mijn Interessegebieden"),
            },
        )
    if profile_config.mentors:
        base_url = reverse("profile:contact_list")
        begeleiders_url = f"{base_url}?{urlencode({'type': 'begeleider'})}"
        cms_profile_pages.append(
            {
                "url": begeleiders_url,
                "link_text": _("Mijn begeleiders"),
            },
        )
    if profile_config.my_contacts:
        cms_profile_pages.append(
            {
                "url_name": "profile:contact_list",
                "link_text": _("Mijn contacten"),
            },
        )
    if (
        profile_config.selfdiagnose
        and QuestionnaireStep.objects.filter(published=True).exists()
    ):
        cms_profile_pages.append(
            {
                "url_name": "products:questionnaire_list",
                "link_text": _("Zelfdiagnose"),
            }
        )
    if profile_config.actions:
        cms_profile_pages.append(
            {
                "url_name": "profile:action_list",
                "link_text": _("Openstaande acties"),
            },
        )
    if profile_config.notifications:
        cms_profile_pages.append(
            {
                "url_name": "profile:notifications",
                "link_text": _("Notificatievoorkeuren"),
            }
        )
    if profile_config.questions:
        cms_profile_pages.append(
            {
                "url_name": "cases:contactmoment_list",
                "link_text": _("Mijn vragen"),
            }
        )
    if profile_config.ssd:
        cms_profile_pages.append(
            {
                "url_name": "ssd:uitkeringen",
                "link_text": _("Mijn uitkeringen"),
            }
        )
    if profile_config.appointments:
        cms_profile_pages.append(
            {
                "url_name": "profile:appointments",
                "link_text": _("Mijn afspraken"),
            },
        )

    return cms_profile_pages


def _get_platform_pages(request) -> list:
    """
    Get platform pages (home, contact form, login) for the sitemap
    """
    platform_pages = [
        {"url_name": "pages-root", "link_text": _("Home page")},
    ]

    klant_config = KlantenSysteemConfig.get_solo()
    if klant_config.contact_registration_enabled:
        platform_pages.append(
            {
                "url_name": "openklant:contactform",
                "link_text": _("Contactformulier"),
            },
        )

    # Hide login links for users that are logged in
    if not request.user.is_authenticated:
        platform_pages.append(
            {"url_name": "login", "link_text": _("Login or create an account")}
        )

    return platform_pages


def _get_cms_footer_pages(request) -> list:
    """
    Get footer CMS pages from site configuration for the sitemap
    """
    config = SiteConfiguration.get_solo()
    cms_footer_pages = config.get_ordered_cms_pages()

    # Filter out auth-required pages for anonymous users
    if not request.user.is_authenticated:
        cms_footer_pages = [
            page
            for page in cms_footer_pages
            if not hasattr(page, "commonextension")
            or not page.commonextension.requires_auth
        ]

    titles = [
        Title.objects.get(page=page, language=page.languages)
        for page in cms_footer_pages
    ]

    return [
        {"url": page.get_absolute_url(), "link_text": title.title}
        for page, title in zip(cms_footer_pages, titles)
    ]


def sitemap(request):
    """
    Collect internal links for display in footer
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
    }

    context["cms_pages"] = _get_cms_pages()
    context["cms_profile_pages"] = _get_cms_profile_pages()
    context["platform_pages"] = _get_platform_pages(request)
    context["cms_footer_pages"] = _get_cms_footer_pages(request)

    return render(request, template_name, context)
