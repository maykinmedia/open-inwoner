import abc

from django.conf import settings
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from furl import furl


def get_always_pass_prefixes() -> tuple[str, ...]:
    return (
        settings.MEDIA_URL,
        settings.PRIVATE_MEDIA_URL,
        settings.STATIC_URL,
        reverse("login"),
        reverse("logout"),
        reverse("kvk:branches"),
        # prefixes from urls.py
        "/admin/",
        "/csp/",
        "/reset/",
        "/api/",
        "/digid/",
        "/eherkenning/",
        "/oidc/",
        "/digid-oidc/",
        "/eherkenning-oidc/",
        "/cms_login/",
        "/cms_wizard/",
    )


def get_app_pass_prefixes() -> tuple[str, ...]:
    """
    Urls for apps that may not be active
    """
    return (
        "profile:registration_necessary",
        "profile:email_verification_user",
    )


def resolve_urls(urls) -> tuple[str, ...]:
    ret = list()
    for url in urls:
        try:
            ret.append(resolve_url(url))
        except NoReverseMatch:
            # support testing without cms app mounted
            pass
    return tuple(ret)


class BaseConditionalUserRedirectMiddleware(abc.ABC):
    """
    Base class for middleware that redirects users to another view based on conditions

    Typical use case is forced registration, verification

    Usually only needs override for `redirect_url` and `requires_redirect(request)`
    """

    redirect_url: str = None
    extra_pass_prefixes: tuple[str, ...] = None

    def __init__(self, get_response):
        self.get_response = get_response

    @abc.abstractmethod
    def requires_redirect(self, request) -> bool:
        return False

    def get_redirect_url(self, request) -> str:
        # redirect_url could be reverse_lazy
        if self.redirect_url is None:
            n = self.__class__.__name__
            raise ValueError(
                f"configure {n}.redirect_url or override {n}.get_redirect_url()"
            )
        return self.redirect_url

    def get_pass_prefixes(self, request) -> tuple[str, ...]:
        """
        URL prefixes we're skipping without checking requires_redirect()
        """
        prefixes = get_always_pass_prefixes()
        prefixes += resolve_urls(get_app_pass_prefixes())
        prefixes += (resolve_url(self.get_redirect_url(request)),)
        prefixes += self.get_extra_pass_prefixes()
        return prefixes

    def get_extra_pass_prefixes(self) -> tuple[str, ...]:
        prefixes = []
        if self.extra_pass_prefixes:
            return resolve_urls(self.extra_pass_prefixes)
        return tuple(prefixes)

    def __call__(self, request):
        # # we could filter on method for safety but it's kludgy
        # if request.method not in ("GET", "HEAD", "OPTIONS"):
        #     return self.get_response(request)

        # we only trigger for authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            # str() to resolve lazy reverses
            target = str(self.get_redirect_url(request))
        except NoReverseMatch:
            # TODO log this or raise (raise problematic if cms-app gets unmounted)
            return self.get_response(request)

        if request.path.startswith(self.get_pass_prefixes(request)):
            return self.get_response(request)

        if target and self.requires_redirect(request):
            url = furl(target)
            # NOTE: this looks odd but exising code could depend on it
            if request.path != settings.LOGIN_REDIRECT_URL:
                url.set({"next": request.path})
            url.args.update(request.GET)
            return redirect(str(url))

        # fallthrough
        return self.get_response(request)
