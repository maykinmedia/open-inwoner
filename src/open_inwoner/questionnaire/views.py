from django.http import HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404
from django.views.generic import FormView

from .forms import QuestionnaireStepForm
from .models import QuestionnaireStep


class QuestionnaireStepView(FormView):
    """
    Shows a step in a questionnaire.
    """
    session_key = 'questionnaire.views.QuestionnaireStepView.object.slug'
    template_name = 'questionnaire/questionnaire-step.html'
    form_class = QuestionnaireStepForm

    def get_object(self) -> QuestionnaireStep:
        slug = self.kwargs.get('slug', self.request.session.get(self.session_key))

        if slug:
            return get_object_or_404(QuestionnaireStep, slug=slug)

        return get_list_or_404(QuestionnaireStep.objects.all())[0]

    def get_form_kwargs(self) -> dict:
        instance = self.get_object()

        return {
            **super().get_form_kwargs(),
            "instance": instance
        }

    def form_valid(self, form: QuestionnaireStepForm):
        try:
            questionnaire_step = form.cleaned_data['answer']
        except (AttributeError, KeyError):
            return self.form_invalid(form)

        self.request.session[self.session_key] = questionnaire_step.slug
        return HttpResponseRedirect(redirect_to=questionnaire_step.get_absolute_url())
