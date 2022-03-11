from django.http import HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404
from django.views.generic import FormView, RedirectView

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


class QuestionnaireStepView(FormView):
    """
    Shows a step in a questionnaire.
    """

    template_name = "questionnaire/questionnaire-step.html"
    form_class = QuestionnaireStepForm

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
