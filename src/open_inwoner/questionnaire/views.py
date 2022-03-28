from typing import Optional

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, RedirectView

from view_breadcrumbs import BaseBreadcrumbMixin

from .forms import QuestionnaireStepForm
from .models import QuestionnaireStep

QUESTIONNAIRE_SESSION_KEY = "questionnaire.views.QuestionnaireStepView.object.slug"


class QuestionnaireResetView(RedirectView):
    """
    Clears the questionnaire session, then redirects to the account's profile page.
    """

    pattern_name = "accounts:my_profile"

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        request.session[QUESTIONNAIRE_SESSION_KEY] = None
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs) -> Optional[str]:
        if not self.request.user.is_authenticated:
            return reverse("root")
        return super().get_redirect_url(*args, **kwargs)


class QuestionnaireStepView(BaseBreadcrumbMixin, FormView):
    """
    Shows a step in a questionnaire.
    """

    template_name = "questionnaire/questionnaire-step.html"
    form_class = QuestionnaireStepForm

    @cached_property
    def crumbs(self):
        if self.request.user.is_authenticated:
            return [
                (_("Mijn profiel"), reverse("accounts:my_profile")),
                (_("Zelfdiagnose"), reverse("questionnaire:index")),
            ]
        return [
            (_("Zelfdiagnose"), reverse("questionnaire:index")),
        ]

    def get_object(self) -> QuestionnaireStep:
        slug = self.kwargs.get(
            "slug", self.request.session.get(QUESTIONNAIRE_SESSION_KEY)
        )

        if slug:
            return get_object_or_404(QuestionnaireStep, slug=slug)

        return get_object_or_404(QuestionnaireStep.objects, is_default=True)

    def get_form_kwargs(self) -> dict:
        instance = self.get_object()

        return {**super().get_form_kwargs(), "instance": instance}

    def form_valid(self, form: QuestionnaireStepForm):
        questionnaire_step = form.cleaned_data["answer"]
        self.request.session[QUESTIONNAIRE_SESSION_KEY] = questionnaire_step.slug
        return HttpResponseRedirect(redirect_to=questionnaire_step.get_absolute_url())
