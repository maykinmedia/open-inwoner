from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

import structlog

from open_inwoner.cms.cases.views.mixins import CaseAccessMixin

from .client import (
    GesprekkenAPIError,
    GesprekkenClient,
    build_gesprekken_client,
    uuid_from_url,
)
from .forms import GespreksbijdrageForm, GesprekStartForm
from .models import MijnGesprekkenConfig
from .services import (
    GesprekFout,
    build_gesprek_view,
    bump_versie,
    fetch_gesprekken_for_zaak,
    get_versie,
    mark_seen,
    partij_url,
    resolve_partij_uuid,
    upload_bijlage,
)

logger = structlog.stdlib.get_logger(__name__)


class GesprekkenSectionMixin(CaseAccessMixin):
    """The 'Mijn gesprekken' section of the zaak detail page, rendered as an htmx fragment."""

    template_name = "pages/cases/gesprekken.html"

    def dispatch(self, request, *args, **kwargs):
        self.config = MijnGesprekkenConfig.get_solo()
        if not self.config.is_active:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @property
    def zaak_gesloten(self) -> bool:
        return bool(getattr(self.zaak, "einddatum", None))

    def kan_starten(self, partij_uuid: str | None) -> bool:
        """A gesprek needs a Partij as verzender and an Actor as ontvanger."""
        return bool(
            self.config.burger_mag_gesprek_starten
            and self.config.heeft_ontvanger
            and partij_uuid
            and not self.zaak_gesloten
        )

    def section_context(
        self,
        tab: str,
        open_gesprek: str | None,
        form=None,
        start_form=None,
        fout: str | None = None,
    ) -> dict:
        zaak_url = self.zaak.url
        versie = get_versie(zaak_url)
        partij_uuid = resolve_partij_uuid(self.request.user)
        client = build_gesprekken_client(self.config)

        error = False
        gesprekken = []
        try:
            gesprekken = [
                (gesprek, build_gesprek_view(gesprek, partij_uuid, self.config))
                for gesprek in fetch_gesprekken_for_zaak(client, zaak_url)
            ]
        except GesprekkenAPIError:
            logger.exception("Could not fetch gesprekken", zaak=zaak_url)
            error = True

        views = [view for _gesprek, view in gesprekken]
        open_views = [v for v in views if v.is_open]
        gesloten_views = [v for v in views if not v.is_open]
        shown = open_views if tab == "open" else gesloten_views
        if open_gesprek is None and shown:
            open_gesprek = shown[0].uuid

        # Seeing a gesprek counts only when it is expanded on screen
        for gesprek, view in gesprekken:
            if view.uuid == open_gesprek:
                mark_seen(client, self.request.user, gesprek, view)

        section_url = reverse(
            "cases:case_detail_gesprekken",
            kwargs={k: self.kwargs[k] for k in ("api_group_id", "object_id")},
        )
        return {
            "gesprekken": shown,
            "tab": tab,
            "open_gesprek": open_gesprek,
            "aantal_open": len(open_views),
            "aantal_gesloten": len(gesloten_views),
            "zaak_gesloten": self.zaak_gesloten,
            "kan_starten": self.kan_starten(partij_uuid),
            "bijlage_toegestaan": self.config.bijlagen_ingeschakeld,
            "form": form or GespreksbijdrageForm(),
            "start_form": start_form or GesprekStartForm(),
            "section_url": section_url,
            "poll_url": f"{section_url}?tab={tab}&open={open_gesprek or ''}&versie={versie}",
            "poll_interval": self.config.polling_interval_seconden,
            "error": error,
            "fout": fout,
        }

    def gesprek_van_zaak(self, client: GesprekkenClient, gesprek_uuid: str) -> dict:
        """The gesprek, which must belong to the zaak the user has access to."""
        try:
            gesprek = client.get_gesprek(gesprek_uuid)
        except GesprekkenAPIError:
            raise Http404 from None

        aanleiding = gesprek.get("aanleidingZaak") or ""
        if aanleiding.rstrip("/") != self.zaak.url.rstrip("/"):
            raise Http404
        return gesprek

    def eigen_open_gesprek(
        self, client: GesprekkenClient, gesprek_uuid: str
    ) -> tuple[dict, str]:
        """
        The gesprek and the deelname of the user, for an action of the user: the
        zaak and the gesprek must be open and the user must take part.
        """
        gesprek = self.gesprek_van_zaak(client, gesprek_uuid)
        if self.zaak_gesloten:
            raise GesprekFout(_("De zaak is gesloten."))
        if gesprek.get("momentEindeGesprek"):
            raise GesprekFout(_("Dit gesprek is gesloten."))

        view = build_gesprek_view(
            gesprek, resolve_partij_uuid(self.request.user), self.config
        )
        if not view.eigen_deelname:
            raise GesprekFout(_("U neemt niet deel aan dit gesprek."))
        return gesprek, view.eigen_deelname

    def bijlagen_uit_form(self, client: GesprekkenClient, form) -> list[dict]:
        if not (bestand := form.cleaned_data.get("bijlage")):
            return []
        if not self.config.bijlagen_ingeschakeld:
            raise GesprekFout(_("Bijlagen zijn niet ingeschakeld."))
        return [upload_bijlage(client, bestand)]

    def render_section(self, tab: str, open_gesprek: str | None, **kwargs):
        context = self.get_context_data()
        context.update(self.section_context(tab, open_gesprek, **kwargs))
        return self.render_to_response(context)


class GesprekkenSectionView(GesprekkenSectionMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Polling: nothing changed since the client's version, so no swap
        if (versie := request.GET.get("versie")) and versie == get_versie(
            self.zaak.url
        ):
            return HttpResponse(status=204)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tab = "gesloten" if self.request.GET.get("tab") == "gesloten" else "open"
        context.update(self.section_context(tab, self.request.GET.get("open") or None))
        return context


class GesprekStartView(GesprekkenSectionMixin, TemplateView):
    """
    Starts a gesprek about the zaak, with the resident as verzender of the first
    bijdrage and the configured Actor as ontvanger, and re-renders the section.
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        partij_uuid = resolve_partij_uuid(request.user)
        if not self.kan_starten(partij_uuid):
            raise PermissionDenied

        form = GesprekStartForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_section(
                "open",
                None,
                start_form=form,
                fout=_("Controleer uw bericht en probeer het opnieuw."),
            )

        try:
            gesprek = self.start_gesprek(form, partij_uuid)
        except GesprekFout as exc:
            return self.render_section("open", None, start_form=form, fout=str(exc))
        return self.render_section("open", gesprek["uuid"])

    def start_gesprek(self, form: GesprekStartForm, partij_uuid: str) -> dict:
        client = build_gesprekken_client(self.config)
        bijlagen = self.bijlagen_uit_form(client, form)
        user = self.request.user
        try:
            gesprek = client.create_gesprek(
                {
                    "gespreksonderwerp": form.cleaned_data["onderwerp"],
                    "aanleidingZaak": self.zaak.url,
                    "ontvanger": [
                        {
                            "type": "actor",
                            "actor": self.config.ontvanger_actor_url,
                            "naam": self.config.ontvanger_actor_naam,
                        }
                    ],
                    "eersteBijdrage": {
                        "tekstGespreksBijdrage": form.cleaned_data["tekst"],
                        "bijlagen": bijlagen,
                        "verzender": {
                            "nieuweDeelname": {
                                "type": "partij",
                                "partij": partij_url(partij_uuid),
                                "naam": user.get_full_name()
                                or user.company_name
                                or _("Inwoner"),
                            }
                        },
                    },
                }
            )
        except GesprekkenAPIError as exc:
            logger.exception("Could not create gesprek", zaak=self.zaak.url)
            raise GesprekFout(
                _("Het starten is mislukt. Probeer het later opnieuw.")
            ) from exc

        bump_versie(self.zaak.url)
        return gesprek


class GesprekBijdrageView(GesprekkenSectionMixin, TemplateView):
    """Places a bijdrage of the resident, with an optional bijlage, and re-renders the section."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        gesprek_uuid = str(kwargs["gesprek_uuid"])
        form = GespreksbijdrageForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_section(
                "open",
                gesprek_uuid,
                form=form,
                fout=_("Controleer uw bericht en probeer het opnieuw."),
            )

        try:
            self.place_bijdrage(gesprek_uuid, form)
        except GesprekFout as exc:
            return self.render_section("open", gesprek_uuid, form=form, fout=str(exc))
        return self.render_section("open", gesprek_uuid)

    def place_bijdrage(self, gesprek_uuid: str, form: GespreksbijdrageForm) -> None:
        client = build_gesprekken_client(self.config)
        gesprek, deelname = self.eigen_open_gesprek(client, gesprek_uuid)
        bijlagen = self.bijlagen_uit_form(client, form)

        try:
            client.create_bijdrage(
                {
                    "gesprek": gesprek["url"],
                    "tekstGespreksBijdrage": form.cleaned_data["tekst"],
                    "bijlagen": bijlagen,
                    "verzender": {"gespreksdeelname": deelname},
                }
            )
        except GesprekkenAPIError as exc:
            logger.exception("Could not create bijdrage", gesprek=gesprek_uuid)
            raise GesprekFout(
                _("Het versturen is mislukt. Probeer het later opnieuw.")
            ) from exc

        bump_versie(self.zaak.url)


class GesprekEindigenView(GesprekkenSectionMixin, TemplateView):
    """Closes a gesprek on behalf of the resident and re-renders the section."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        gesprek_uuid = str(kwargs["gesprek_uuid"])
        client = build_gesprekken_client(self.config)
        try:
            self.eigen_open_gesprek(client, gesprek_uuid)
            self.eindig_gesprek(client, gesprek_uuid)
        except GesprekFout as exc:
            return self.render_section("open", gesprek_uuid, fout=str(exc))
        return self.render_section("gesloten", gesprek_uuid)

    def eindig_gesprek(self, client: GesprekkenClient, gesprek_uuid: str) -> None:
        try:
            client.eindig_gesprek(gesprek_uuid)
        except GesprekkenAPIError as exc:
            logger.exception("Could not close gesprek", gesprek=gesprek_uuid)
            raise GesprekFout(
                _("Het afsluiten is mislukt. Probeer het later opnieuw.")
            ) from exc
        bump_versie(self.zaak.url)


class GesprekBijlageDownloadView(GesprekkenSectionMixin, TemplateView):
    """
    Downloads a bijlage of a gespreksbijdrage.

    The bestand is not linked to the zaak, so the case document download does not
    apply. Access follows from the gesprek instead: the gesprek must have this zaak
    as aanleiding and one of its bijdragen must carry the bestand. The portal holds
    the rights towards the API, so this check is what protects the bestand.
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        client = build_gesprekken_client(self.config)
        gesprek = self.gesprek_van_zaak(client, str(kwargs["gesprek_uuid"]))

        file_id = str(kwargs["file_id"])
        if not any(
            uuid_from_url(bijlage["bestand"]) == file_id
            for bijdrage in gesprek.get("gespreksbijdragen", [])
            for bijlage in bijdrage.get("bijlagen", [])
        ):
            raise PermissionDenied

        try:
            download_url = client.get_bestand(file_id).get("downloadUrl")
        except GesprekkenAPIError:
            raise Http404 from None
        if not download_url:
            raise Http404

        # A temporary URL of the storage, so the file does not pass through the portal
        return HttpResponseRedirect(download_url)
