import logging

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

from open_inwoner.openzaak.models import ZGWApiGroupConfig

logger = logging.getLogger(__name__)


class LegacyCaseDetailHandler(View):
    """Redirect the legacy case detail to the current version with ZGW API group ref."""

    def get(
        self,
        request: HttpRequest,
        object_id: str,
    ):
        redirect_url = None
        match ZGWApiGroupConfig.objects.count():
            case 1:
                target_api_group = ZGWApiGroupConfig.objects.get()
                redirect_url = reverse(
                    "cases:case_detail",
                    kwargs={
                        "api_group_id": target_api_group.id,
                        "object_id": object_id,
                    },
                )
            case count if count > 1:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "The link you clicked on has expired. Please find your case in the"
                        " list below."
                    ),
                )
                logger.warning(
                    "Could not automatically handle legacy case detail URL due to multiple"
                    " ZGWApiGroupConfig objects"
                )
                redirect_url = reverse("cases:index")
            case 0:
                # This is an invariant violation: there should always be at least
                # one ZGWApiGroupConfig.
                logger.error(
                    "Legacy redirect invoked without any configured API groups"
                )
                raise Http404

        return HttpResponseRedirect(redirect_url)
