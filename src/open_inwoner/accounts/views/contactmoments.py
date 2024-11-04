import logging
from typing import Iterable, Protocol

from django.contrib.auth.mixins import AccessMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.models import User
from open_inwoner.openklant.models import KlantContactMomentAnswer
from open_inwoner.openklant.services import (
    KlantenService,
    Question,
    QuestionValidator,
    ZaakWithApiGroup,
    eSuiteKlantenService,
    eSuiteVragenService,
)
from open_inwoner.openklant.views.contactform import ContactFormView
from open_inwoner.openklant.wrap import FetchParameters
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

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("pages-root"))
        else:
            return super().handle_no_permission()


class VragenService(Protocol):
    def list_questions(
        self,
        fetch_params: FetchParameters,
        user: User,
    ) -> Iterable[Question]:  # noqa: E704
        ...

    def retrieve_question(
        self,
        fetch_params: FetchParameters,
        question_uuid: str,
        user: User,
    ) -> tuple[Question | None, ZaakWithApiGroup | None]:  # noqa: E704
        ...

    def get_fetch_parameters(
        self,
        request=None,
        user: User | None = None,
        use_vestigingsnummer: bool = False,
    ) -> FetchParameters | None:  # noqa: E704
        ...


class KlantContactMomentBaseView(
    CommonPageMixin, BaseBreadcrumbMixin, KlantContactMomentAccessMixin, TemplateView
):
    def get_service(self) -> VragenService:
        # TODO: Refactor to support both OpenKlant2 and eSuite services at once
        return eSuiteVragenService()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["anchors"] = self.get_anchors()
        return ctx

    def get_fetch_params(self, service: VragenService):
        if not (
            fetch_params := service.get_fetch_parameters(
                self.request, use_vestigingsnummer=True
            )
        ):
            raise ValueError("User has no bsn or kvk attributes")

        return fetch_params


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
        service = self.get_service()
        questions = service.list_questions(
            self.get_fetch_params(service), user=self.request.user
        )
        ctx["contactmomenten"] = [
            QuestionValidator.validate_python(q) for q in questions
        ]
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
        service = self.get_service()

        kcm, zaak = service.retrieve_question(
            self.get_fetch_params(service), kwargs["kcm_uuid"], user=self.request.user
        )
        if not kcm:
            raise Http404()

        QuestionValidator.validate_python(kcm)

        local_kcm, created = KlantContactMomentAnswer.objects.get_or_create(  # noqa
            user=self.request.user, contactmoment_url=kcm["case_detail_url"]
        )
        if not local_kcm.is_seen:
            local_kcm.is_seen = True
            local_kcm.save()

        contactmoment = kcm
        ctx["contactmoment"] = contactmoment
        ctx["zaak"] = zaak.zaak if zaak else None
        case_url = (
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(zaak.zaak.uuid),
                    "api_group_id": zaak.api_group.id,
                },
            )
            if zaak
            else None
        )
        ctx["metrics"] = [
            {
                "label": _("Status: "),
                "value": contactmoment["status"],
            },
            {
                "label": _("Ingediend op: "),
                "value": contactmoment["registered_date"],
            },
            {
                "label": _("Vraag nummer: "),
                "value": contactmoment["identification"],
            },
            {
                "label": _("Contact gehad via: "),
                "value": contactmoment["channel"],
            },
        ]
        origin = self.request.headers.get("Referer")
        if origin and reverse("cases:contactmoment_list") in origin:
            ctx["origin"] = {
                "label": _("Terug naar overzicht"),
                "url": origin,
            }
            if zaak:
                ctx["destination"] = {
                    "label": _("Naar aanvraag"),
                    "url": case_url,
                }
        else:
            ctx["origin"] = {
                "label": _("Terug naar aanvraag"),
                "url": case_url,
            }
            ctx["destination"] = {
                "label": _("Bekijk alle vragen"),
                "url": reverse("cases:contactmoment_list"),
            }
        return ctx


class KlantContactMomentRedirectView(KlantContactMomentAccessMixin, View):
    """
    Redirect to `KlantContactMomentDetailView` on the basis of contactmoment uuid
    """

    def get(self, request, *args, **kwargs):
        vragen_service: VragenService = eSuiteVragenService()
        klanten_service: KlantenService = eSuiteKlantenService()
        fetch_params = klanten_service.get_fetch_parameters(self.request)

        klant = klanten_service.retrieve_klant(**fetch_params)
        kcms = vragen_service.retrieve_klantcontactmomenten_for_klant(klant)

        if not kcms:
            raise Http404

        contactmoment_uuid = kwargs["uuid"]
        kcm = next(
            kcm for kcm in kcms if str(kcm.contactmoment.uuid) == contactmoment_uuid
        )

        if not kcm:
            raise Http404

        return HttpResponseRedirect(
            reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": kcm.uuid})
        )
