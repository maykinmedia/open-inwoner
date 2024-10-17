from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.views import View

from open_inwoner.berichten.api_models import Bericht
from open_inwoner.berichten.services import BerichtenService


class RequireBsnMixin(AccessMixin, View):

    request: HttpRequest
    bericht: Bericht

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.bsn:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return TemplateResponse(self.request, "pages/cases/403.html")

        return super().handle_no_permission()


class BerichtAccessMixin(AccessMixin, View):

    request: HttpRequest
    bericht: Bericht

    def dispatch(self, request, *args, **kwargs):
        if not (bsn := getattr(request.user, "bsn", None)):
            return super().handle_no_permission()

        service = BerichtenService()
        self.bericht = service.fetch_bericht(self.kwargs["object_uuid"])
        if (
            self.bericht.identificatie.type != "bsn"
            or self.bericht.identificatie.value != bsn
        ):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return TemplateResponse(self.request, "pages/cases/403.html")

        return super().handle_no_permission()
