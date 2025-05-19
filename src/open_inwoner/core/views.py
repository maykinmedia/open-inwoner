from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse

from open_inwoner.accounts.models import User
from open_inwoner.cms.utils.page_display import (
    benefits_page_is_published,
    case_page_is_published,
    collaborate_page_is_published,
    inbox_page_is_published,
    products_page_is_published,
    profile_page_is_published,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models.category import Category


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
            {"url_name": "ssd:uitkeringen", "link_text": "Mijn uitkeringen"}
        )
    if case_page_is_published():
        context["cms_pages"].append(
            {"url_name": "cases:index", "link_text": "Mijn zaken"}
        )
        context["cms_pages"].append(
            {"url_name": "cases:contactmoment_list", "link_text": "Mijn vragen"}
        )
    if collaborate_page_is_published():
        context["cms_pages"].append(
            {"url_name": "collaborate:plan_list", "link_text": "Mijn samenwerkingen"}
        )
    if inbox_page_is_published():
        context["cms_pages"].append(
            {"url_name": "inbox:index", "link_text": "Mijn berichten"}
        )
    if products_page_is_published():
        context["cms_pages"].append(
            {"url_name": "products:questionnaire_list", "link_text": "Zelftest"}
        )
    if profile_page_is_published():
        base_url = reverse("profile:contact_list")
        begeleiders_url = f"{base_url}?{urlencode({'type': 'begeleider'})}"

        context["cms_profile_pages"] = [
            {"url_name": "profile:detail", "link_text": "Mijn profiel"},
            {
                "url_name": "profile:categories",
                "link_text": "Mijn interessegebieden",
            },
            {
                "url": begeleiders_url,
                "link_text": "Mijn begeleiders",
            },
            {"url_name": "profile:contact_list", "link_text": "Mijn contacten"},
            {"url_name": "profile:appointments", "link_text": "Mijn afspraken"},
            {"url_name": "profile:action_list", "link_text": "Openstaande acties"},
        ]

    # add "platform pages" (conditional login/register page, cookie info etc.)
    context["platform_pages"] = [
        {"url_name": "pages-root", "link_text": "Home page"},
        {"url_name": "contactform", "link_text": "Contactformulier"},
    ]

    # hide login links for users that are logged in
    if not request.user.is_authenticated:
        context["platform_pages"].append(
            {"url_name": "login", "link_text": "Login or create an account"}
        )

    # add flatpages to platform_pages
    config = SiteConfiguration.get_solo()
    flatpages = (
        config.get_ordered_flatpages
        if request.user.is_authenticated
        else config.get_ordered_flatpages.filter(registration_required=False)
    )
    context["flatpages"] = [
        {"url": page.url, "link_text": page.title} for page in flatpages
    ]

    return render(request, template_name, context)
