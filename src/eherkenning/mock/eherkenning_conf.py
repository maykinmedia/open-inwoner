from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.encoding import force_str


def get_app_title():
    """
    Title of application to display in IDP view
    """
    return force_str(
        getattr(settings, "EHERKENNING_MOCK_APP_TITLE", "") or "eHerkenning Mock Login"
    )


def get_success_url():
    """
    Default URL to redirect to after login
    """
    url = (
        getattr(settings, "EHERKENNING_MOCK_RETURN_URL", "")
        or getattr(settings, "LOGIN_REDIRECT_URL", "")
        or "/"
    )
    return resolve_url(url)


def get_cancel_url():
    """
    Default URL if user presses 'vorige/back' in IDP view
    """
    url = (
        getattr(settings, "EHERKENNING_MOCK_CANCEL_URL", "")
        or getattr(settings, "LOGIN_URL", "")
        or "/"
    )
    return resolve_url(url)


def get_idp_login_url():
    """
    URL of the IDP login page (possibly on other domain)
    """
    url = getattr(settings, "EHERKENNING_MOCK_IDP_LOGIN_URL", "") or reverse(
        "eherkenning-mock:login"
    )
    return resolve_url(url)
