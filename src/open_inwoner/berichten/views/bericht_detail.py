import logging

from django.http import Http404, HttpResponseRedirect, StreamingHttpResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.berichten.services import BerichtenService
from open_inwoner.berichten.views.mixins import BerichtAccessMixin
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.utils.views import CommonPageMixin

logger = logging.getLogger(__name__)


class BerichtDetailView(
    CommonPageMixin,
    BaseBreadcrumbMixin,
    TemplateView,
    BerichtAccessMixin,
):

    template_name = "pages/berichten/detail.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn berichten"), reverse("berichten:list")),
            (_("Bericht"), reverse("berichten:detail", kwargs=self.kwargs)),
        ]

    def page_title(self):
        return _("Mijn berichten")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = BerichtenService()
        context["bericht"] = self.bericht
        if not self.bericht.geopend:
            service.update_object(self.kwargs["object_uuid"], {"geopend": True})

        return context


class MarkBerichtUnreadView(BerichtAccessMixin):
    def get(self, *args, **kwargs):
        service = BerichtenService()
        service.update_object(self.kwargs["object_uuid"], {"geopend": False})
        return HttpResponseRedirect(reverse("berichten:list"))


class BerichtDownloadView(BerichtAccessMixin):
    def get(self, *args, **kwargs):
        url = self.request.GET.get("url")
        if not url:
            logger.error("No URL provided")
            raise Http404

        if url not in self.bericht.bijlages:
            logger.error("URL provided that is not a bijlage for the specified bericht")
            raise Http404

        try:
            api_group = ZGWApiGroupConfig.objects.resolve_group_from_hints(url=url)
        except ZGWApiGroupConfig.DoesNotExist:
            logger.exception("Unable to resolve API group from bericht attachment url")
            raise Http404

        documenten_client = api_group.documenten_client
        info_object = documenten_client._fetch_single_information_object(url=url)
        logger.info(f"{info_object=}")
        if not info_object:
            logger.error("Could not find info object for bericht attachment")
            raise Http404

        content_stream = api_group.documenten_client.download_document(
            info_object.inhoud
        )
        logger.info(f"{content_stream=} {content_stream.headers=}")

        if not content_stream:
            logger.error("Could not build content stream for bericht attachment")
            raise Http404

        headers = {
            "Content-Disposition": f'attachment; filename="{info_object.bestandsnaam}"',
            "Content-Type": info_object.formaat,
            # TODO: We should be able to use info_object.bestandsomvang here, but we've seen instances
            # in the wild where this is incorrectly set, which can trip up the browser. Better to just
            # use the content-length given to us by the server.
            "Content-Length": content_stream.headers.get("Content-Length"),
        }
        response = StreamingHttpResponse(content_stream, headers=headers)
        return response
