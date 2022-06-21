from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView

from open_inwoner.utils.views import LogMixin

from ..forms import DocumentForm
from ..models import Document


class DocumentCreateView(LogMixin, LoginRequiredMixin, CreateView):
    template_name = "pages/profile/documents/edit.html"
    model = Document
    form_class = DocumentForm
    success_url = reverse_lazy("accounts:my_profile")

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(owner=self.request.user)

    def form_valid(self, form):
        self.object = form.save(self.request.user)

        self.log_user_action(self.object, _("file was uploaded"))
        return HttpResponseRedirect(self.get_success_url())


class DocumentDeleteView(LogMixin, LoginRequiredMixin, DeleteView):
    template_name = "pages/profile/documents/delete.html"
    model = Document
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("accounts:my_profile")

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        object = self.get_object()
        super().delete(request, *args, **kwargs)

        self.log_deletion(object, _("file was deleted"))
        return HttpResponseRedirect(self.success_url)
