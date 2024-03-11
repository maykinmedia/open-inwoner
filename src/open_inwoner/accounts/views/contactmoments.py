import logging
from datetime import datetime
from typing import Optional, TypedDict

from django.contrib.auth.mixins import AccessMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openklant.api_models import KlantContactMoment
from open_inwoner.openklant.clients import build_client
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import ContactFormSubject
from open_inwoner.openklant.views.contactform import ContactFormView
from open_inwoner.openklant.wrap import (
    fetch_klantcontactmoment,
    fetch_klantcontactmomenten,
    get_fetch_parameters,
)
from open_inwoner.openzaak.clients import build_client as build_client_openzaak
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

logger = logging.getLogger(__name__)


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

        if not request.user.bsn and not request.user.kvk:
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
            "status": Status.safe_label(kcm.contactmoment.status, _("Onbekend")),
            "antwoord": kcm.contactmoment.antwoord,
        }

        # replace e_suite_subject_code with OIP configured subject, if applicable
        e_suite_subject_code = getattr(kcm.contactmoment, "onderwerp", None)

        data["onderwerp"] = self.get_kcm_subject(kcm, e_suite_subject_code)

        return data

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["anchors"] = self.get_anchors()
        return ctx

    def get_kcm_subject(
        self,
        kcm: KlantContactMoment,
        e_suite_subject_code: str,
    ) -> Optional[str]:
        """
        Try to determine the subject ('onderwerp') of a contactmoment
        """
        if not e_suite_subject_code:
            return None

        try:
            subject = ContactFormSubject.objects.get(subject_code=e_suite_subject_code)
        except (
            ContactFormSubject.DoesNotExist,
            ContactFormSubject.MultipleObjectsReturned,
        ) as exc:
            logger.warning(
                "Could not determine subject ('onderwerp') for contactmoment %s",
                kcm.contactmoment.url,
                exc_info=exc,
            )
            return None

        return subject.subject


class KlantContactMomentListView(
    PaginationMixin, ContactFormView, KlantContactMomentBaseView
):
    """
    Display "contactmomenten" (questions), and a form (via ContactFormView) to send a new question
    """

    template_name = "pages/contactmoment/list.html"
    paginate_by = 9

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
        kcms = fetch_klantcontactmomenten(
            **get_fetch_parameters(self.request, use_vestigingsnummer=True)
        )
        ctx["contactmomenten"] = [self.get_kcm_data(kcm) for kcm in kcms]
        paginator_dict = self.paginate_with_context(ctx["contactmomenten"])
        ctx.update(paginator_dict)
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

        kcm = fetch_klantcontactmoment(
            kwargs["kcm_uuid"],
            **get_fetch_parameters(self.request, use_vestigingsnummer=True),
        )

        if not kcm:
            raise Http404()

        if client := build_client("contactmomenten"):
            zaken_client = build_client_openzaak("zaak")
            ocm = client.retrieve_objectcontactmoment(
                kcm.contactmoment, "zaak", zaken_client
            )
            ctx["zaak"] = getattr(ocm, "object", None)

        contactmoment: KCMDict = self.get_kcm_data(kcm)
        ctx["contactmoment"] = contactmoment
        ctx["metrics"] = [
            {
                "label": _("Ontvangstdatum: "),
                "value": contactmoment["registered_date"],
            },
            {
                "label": _("Contactwijze: "),
                "value": contactmoment["channel"],
            },
            {
                "label": _("Status: "),
                "value": contactmoment["status"],
            },
        ]
        return ctx
