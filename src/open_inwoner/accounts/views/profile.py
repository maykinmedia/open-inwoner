from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.forms import Form
from django.urls.base import reverse_lazy
from django.views.generic import FormView, UpdateView

from open_inwoner.accounts.choices import StatusChioces

from ..forms import ThemesForm
from ..models import User


class MyProfileView(LoginRequiredMixin, FormView):
    template_name = "pages/profile/me.html"
    form_class = Form
    success_url = reverse_lazy("accounts:my_profile")

    def get_context_data(self, **kwargs):
        contact_names = [
            f"{contact.first_name} ({contact.get_type_display()})"
            for contact in self.request.user.contacts.all()[:3]
        ]

        context = super().get_context_data(**kwargs)
        context["files"] = self.request.user.documents.all()
        context["theme_text"] = ", ".join(
            list(self.request.user.selected_themes.values_list("name", flat=True))
        )
        context[
            "action_text"
        ] = f"{self.request.user.actions.filter(status=StatusChioces.open).count()} acties staan open."
        context[
            "contact_text"
        ] = f"{', '.join(contact_names)}{'...' if self.request.user.contacts.count() > 3 else ''}"
        return context


class MyCategoriesView(UpdateView):
    template_name = "pages/profile/categories.html"
    model = User
    form_class = ThemesForm
    success_url = reverse_lazy("accounts:my_profile")

    def get_object(self):
        return self.request.user
