import logging
from urllib.parse import urlencode

from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from furl import furl

from eherkenning.mock import eherkenning_conf as conf
from eherkenning.mock.idp.forms import eHerkenningPasswordLoginForm

logger = logging.getLogger(__name__)


class _BaseIDPViewMixin(TemplateView):
    page_title = "eHerkenning: Inloggen"

    def dispatch(self, request, *args, **kwargs):
        # we pass these variables through the URL instead of dealing with POST and sessions
        self.acs_url = self.request.GET.get("acs")
        self.next_url = self.request.GET.get("next")
        self.cancel_url = self.request.GET.get("cancel") or self.request.GET.get(
            "next", ""
        )

        if not self.acs_url:
            logger.debug("missing 'acs' parameter")
            return HttpResponseBadRequest("missing 'acs' parameter")
        if not self.next_url:
            logger.debug("missing 'next' parameter")
            return HttpResponseBadRequest("missing 'next' parameter")
        if not self.cancel_url:
            logger.debug("missing 'cancel' parameter")
            return HttpResponseBadRequest("missing 'cancel' parameter")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            "app_title": conf.get_app_title(),
            "page_title": self.page_title,
            **super().get_context_data(**kwargs),
        }


class eHerkenningMockIDPLoginView(_BaseIDPViewMixin):
    """
    Login method choices pages
    """

    template_name = "eherkenning/mock/eherkenning_login.html"
    page_title = "eHerkenning: Inloggen | Keuze"

    def get_context_data(self, **kwargs):
        params = {
            "acs": self.acs_url,
            "next": self.next_url,
            "cancel": self.cancel_url,
        }
        return {
            "cancel_url": params["cancel"],
            "password_login_url": f"{reverse('eherkenning-mock:password')}?{urlencode(params)}",
            **super().get_context_data(**kwargs),
        }


class eHerkenningMockIDPPasswordLoginView(_BaseIDPViewMixin, FormView):
    """
    Username/password login page
    """

    template_name = "eherkenning/mock/eherkenning_password.html"
    page_title = "eHerkenning: Inloggen | Gebruikersnaam en wachtwoord"

    form_class = eHerkenningPasswordLoginForm

    def form_valid(self, form):
        self.kvk = form.cleaned_data["auth_name"]
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        params = {
            "acs": self.acs_url,
            "next": self.next_url,
            "cancel": self.cancel_url,
        }
        return {
            "action_url": f"{reverse('eherkenning-mock:password')}?{urlencode(params)}",
            "back_url": f"{reverse('eherkenning-mock:login')}?{urlencode(params)}",
            **super().get_context_data(**kwargs),
        }

    def get_success_url(self):
        params = {
            "next": self.next_url,
            "kvk": str(self.kvk),
        }
        success_url = furl(self.acs_url)
        success_url.args.update(params)
        return str(success_url)
