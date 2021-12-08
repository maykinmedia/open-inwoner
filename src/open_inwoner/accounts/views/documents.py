from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.views.generic import CreateView, DeleteView

from ..forms import DocumentForm
from ..models import Document


class DocumentCreateView(CreateView):
    template_name = "pages/profile/documents/edit.html"
    model = Document
    form_class = DocumentForm
    success_url = reverse_lazy("accounts:my_profile")

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class DocumentDeleteView(DeleteView):
    template_name = "pages/profile/documents/delete.html"
    model = Document
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("accounts:my_profile")
