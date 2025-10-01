import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404, StreamingHttpResponse
from django.utils.translation import gettext_lazy as _
from django.views import View

from open_inwoner.openzaak.documents import fetch_single_information_object_uuid
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig
from open_inwoner.openzaak.utils import is_info_object_visible
from open_inwoner.utils.views import LogMixin

from ..mixins import CaseAccessMixin

logger = logging.getLogger(__name__)


class CaseDocumentDownloadView(LogMixin, CaseAccessMixin, View):
    def get(self, request, *args, **kwargs):
        if not self.case:
            raise Http404

        try:
            api_group = ZGWApiGroupConfig.objects.get(pk=self.kwargs["api_group_id"])
        except ZGWApiGroupConfig.DoesNotExist as exc:
            logger.exception("Non-existent ZGWApiGroupConfig passed")
            raise Http404 from exc

        info_object_uuid = kwargs["info_id"]
        info_object = fetch_single_information_object_uuid(
            info_object_uuid, api_group.documenten_client
        )
        if not info_object:
            raise Http404

        # check if this info_object belongs to this case
        if not api_group.zaken_client.fetch_case_information_objects_for_case_and_info(
            self.case.url, info_object.url
        ):
            raise PermissionDenied()

        # check if this info_object should be visible
        config = OpenZaakConfig.get_solo()
        if not is_info_object_visible(info_object, config.document_max_confidentiality):
            raise PermissionDenied()

        # retrieve and stream content
        content_stream = None
        content_stream = api_group.documenten_client.download_document(
            info_object.inhoud
        )

        if not content_stream:
            raise Http404

        self.log_user_action(
            self.request.user,
            _("Document van zaak gedownload {case}: {filename}").format(
                case=self.case.identificatie,
                filename=info_object.bestandsnaam,
            ),
        )

        headers = {
            "Content-Disposition": f'attachment; filename="{info_object.bestandsnaam}"',
            "Content-Type": info_object.formaat,
            "Content-Length": info_object.bestandsomvang,
        }
        response = StreamingHttpResponse(content_stream, headers=headers)
        return response

    def handle_no_permission(self):
        # plain error and no redirect
        raise PermissionDenied()
