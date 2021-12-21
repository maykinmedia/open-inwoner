from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.views.generic import CreateView, ListView
from django.views.generic.edit import UpdateView

from ..forms import ActionForm
from ..models import Action


class ActionListView(LoginRequiredMixin, ListView):
    template_name = "pages/profile/actions/list.html"
    model = Action
    paginate_by = 10

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)


class ActionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "pages/profile/actions/edit.html"
    model = Action
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = ActionForm
    success_url = reverse_lazy("accounts:action_list")

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class ActionCreateView(LoginRequiredMixin, CreateView):
    template_name = "pages/profile/actions/edit.html"
    model = Action
    form_class = ActionForm
    success_url = reverse_lazy("accounts:action_list")

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())
