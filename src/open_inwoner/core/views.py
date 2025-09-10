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


def sitemap(request):
    template_name = "pages/sitemap/sitemap.html"

    # add onderwerpen/categories
    root_categories = (
        Category.get_root_nodes().published().visible_for_user(request.user)
    )
    context = {
        "category_nodes": [
            _get_category_data_for_user(category, request.user)
            for category in root_categories
        ],
    }

    # add CMS pages
    context["cms_pages"] = []
    if benefits_page_is_published():
        context["cms_pages"].append(
            {"url_name": "ssd:uitkeringen", "link_text": _("Mijn uitkeringen")}
        )
    if case_page_is_published():
        context["cms_pages"].append(
            {"url_name": "cases:index", "link_text": _("Mijn zaken")}
        )
        context["cms_pages"].append(
            {"url_name": "cases:contactmoment_list", "link_text": _("Mijn vragen")}
        )
    if collaborate_page_is_published():
        context["cms_pages"].append(
            {"url_name": "collaborate:plan_list", "link_text": _("Mijn samenwerkingen")}
        )
    if inbox_page_is_published():
        context["cms_pages"].append(
            {"url_name": "inbox:index", "link_text": _("Mijn berichten")}
        )
    if products_page_is_published():
        context["cms_pages"].append(
            {"url_name": "products:questionnaire_list", "link_text": _("Zelftest")}
        )
    if profile_page_is_published():
        context["cms_profile_pages"] = [
            {"url_name": "profile:detail", "link_text": _("Mijn profiel")},
        ]

        # conditionally add cms pages based on apphook configuration
        cms_pages = context["cms_profile_pages"]
        try:
            profile_config = ProfileConfig.objects.get()
        except ProfileConfig.MultipleObjectsReturned:
            logger.warning("Multiple instances of ProfileConfig apphook found")
            profile_config = ProfileConfig.objects.first()
        if profile_config.selected_categories:
            cms_pages.append(
                {
                    "url_name": "profile:categories",
                    "link_text": _("Mijn Interessegebieden"),
                },
            )
        if profile_config.mentors:
            base_url = reverse("profile:contact_list")
            begeleiders_url = f"{base_url}?{urlencode({'type': 'begeleider'})}"
            cms_pages.append(
                {
                    "url": begeleiders_url,
                    "link_text": _("Mijn begeleiders"),
                },
            )
        if profile_config.my_contacts:
            cms_pages.append(
                {
                    "url_name": "profile:contact_list",
                    "link_text": _("Mijn contacten"),
                },
            )
        if (
            profile_config.selfdiagnose
            and QuestionnaireStep.objects.filter(published=True).exists()
        ):
            cms_pages.append(
                {
                    "url_name": "products:questionnaire_list",
                    "link_text": _("Zelfdiagnose"),
                }
            )
        if profile_config.actions:
            cms_pages.append(
                {
                    "url_name": "profile:action_list",
                    "link_text": _("Openstaande acties"),
                },
            )
        if profile_config.notifications:
            cms_pages.append(
                {
                    "url_name": "profile:notifications",
                    "link_text": _("Notificatievoorkeuren"),
                }
            )
        if profile_config.questions:
            cms_pages.append(
                {
                    "url_name": "cases:contactmoment_list",
                    "link_text": _("Mijn vragen"),
                }
            )
        if profile_config.ssd:
            cms_pages.append(
                {
                    "url_name": "ssd:uitkeringen",
                    "link_text": _("Mijn uitkeringen"),
                }
            )
        if profile_config.appointments:
            cms_pages.append(
                {
                    "url_name": "profile:appointments",
                    "link_text": _("Mijn afspraken"),
                },
            )

    # add "platform pages" (conditional login/register page, cookie info etc.)
    context["platform_pages"] = [
        {"url_name": "pages-root", "link_text": _("Home page")},
    ]

    klant_config = KlantenSysteemConfig.get_solo()
    if klant_config.contact_registration_enabled:
        context["platform_pages"].append(
            {
                "url_name": "contactform",
                "link_text": _("Contactformulier"),
            },
        )

    # hide login links for users that are logged in
    if not request.user.is_authenticated:
        context["platform_pages"].append(
            {"url_name": "login", "link_text": _("Login or create an account")}
        )

    # add cms_pages to platform_pages
    config = SiteConfiguration.get_solo()
    cms_pages = config.get_ordered_cms_pages()

    if not request.user.is_authenticated:
        for page in cms_pages:
            if hasattr(page, "commonextension") and page.commonextension.requires_auth:
                cms_pages.remove(page)

    titles = [
        Title.objects.get(page=page, language=page.languages) for page in cms_pages
    ]

    context["cms_pages"] = [
        {"url": page.get_absolute_url(), "link_text": title.title}
        for page, title in zip(cms_pages, titles)
    ]

    return render(request, template_name, context)
