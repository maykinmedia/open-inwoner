from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView

from open_inwoner.utils.views import LogMixin

from ..models import Document


class DocumentDeleteView(LogMixin, LoginRequiredMixin, DeleteView):
    template_name = "pages/profile/documents/delete.html"
    model = Document
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("profile:detail")

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        object = self.get_object()
        super().delete(request, *args, **kwargs)

        self.log_deletion(object, _("file was deleted"))
        return HttpResponseRedirect(self.success_url)
