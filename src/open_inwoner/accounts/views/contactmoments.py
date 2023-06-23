from datetime import datetime
from typing import List, TypedDict

from django.contrib.auth.mixins import AccessMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openklant.api_models import KlantContactMoment
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.wrap import (
    fetch_klantcontactmoment_for_bsn,
    fetch_klantcontactmomenten_for_bsn,
)
from open_inwoner.utils.views import CommonPageMixin


class KlantContactMomentAccessMixin(AccessMixin):
    """
    Shared authorisation check

    Base checks:
    - user is authenticated
    - user has a BSN

    # When retrieving a case :
    # - users BSN has a role for this case
    # - case confidentiality is not higher than globally configured
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.bsn:
            return self.handle_no_permission()

        # TODO more here?

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("pages-root"))
        else:
            return super().handle_no_permission()


class KCMDict(TypedDict):
    registered_date: datetime
    channel: str
    text: str
    url: str
    identificatie: str
    type: str
    onderwerp: str
    status: str
    antwoord: str


class KlantContactMomentBaseView(
    CommonPageMixin, BaseBreadcrumbMixin, KlantContactMomentAccessMixin, TemplateView
):
    def get_kcm_data(self, kcm: KlantContactMoment) -> KCMDict:
        data = {
            "registered_date": kcm.contactmoment.registratiedatum,
            "channel": kcm.contactmoment.kanaal.title(),
            "text": kcm.contactmoment.tekst,
            "url": reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": kcm.uuid}),
            # eSuite extra
            "identificatie": kcm.contactmoment.identificatie,
            "type": kcm.contactmoment.type,
            "onderwerp": kcm.contactmoment.onderwerp,
            "status": Status.safe_label(kcm.contactmoment.status, _("Onbekend")),
            "antwoord": kcm.contactmoment.antwoord,
        }
        return data

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["anchors"] = self.get_anchors()
        return ctx


class KlantContactMomentListView(KlantContactMomentBaseView):
    template_name = "pages/contactmoment/list.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn vragen"), reverse("cases:contactmoment_list"))]

    def page_title(self):
        return _("Mijn vragen")

    def get_anchors(self) -> list:
        return [
            ("#contactmomenten", _("Mijn vragen")),
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kcms = fetch_klantcontactmomenten_for_bsn(self.request.user.bsn)
        ctx["contactmomenten"] = [self.get_kcm_data(kcm) for kcm in kcms]
        return ctx


class KlantContactMomentDetailView(KlantContactMomentBaseView):
    template_name = "pages/contactmoment/detail.html"

    @cached_property
    def crumbs(self):
        return [(_("Mijn vragen"), reverse("cases:contactmoment_list"))]

    def page_title(self):
        return _("Mijn vraag")

    def get_anchors(self) -> list:
        return [
            ("#contactmomenten-details", _("Details")),
            ("#contactmomenten-vraag", _("Vraag")),
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kcm = fetch_klantcontactmoment_for_bsn(
            kwargs["kcm_uuid"], self.request.user.bsn
        )
        if not kcm:
            raise Http404()

        ctx["contactmoment"] = self.get_kcm_data(kcm)
        return ctx
