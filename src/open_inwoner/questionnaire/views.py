from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_list_or_404
from django.views.generic import FormView

from .models import QuestionnaireStep


class QuestionnaireStepChoiceField(forms.ModelChoiceField):
    """
    The ModelChoiceField specific to QuestionnaireStep with a customized label.
    """
    def label_from_instance(self, obj):
        return obj.parent_answer


class QuestionnaireStepForm(forms.Form):
    """
    The form with possible answers for a questionnaire step.
    """
    answer = QuestionnaireStepChoiceField(queryset=QuestionnaireStep.objects.none(), widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs) -> None:
        self.instance = kwargs.pop("instance")
        super().__init__(*args, **kwargs)

        if self.instance:
            children = self.instance.get_children()
            if children:
                self.fields['answer'].queryset = self.instance.get_children()
                return

        self.fields.pop("answer")

    class Meta:
        model = QuestionnaireStep


class QuestionnaireStepView(FormView):
    """
    Shows a step in a questionnaire.
    """
    session_key = 'questionnaire.views.QuestionnaireStepView.object.pk'
    template_name = 'questionnaire/questionnaire-step.html'
    form_class = QuestionnaireStepForm

    def get_object(self) -> QuestionnaireStep:
        slug = self.kwargs.get('slug', self.request.session.get(self.session_key))

        if slug:
            try:
                return QuestionnaireStep.objects.get(slug=slug)
            except QuestionnaireStep.DoesNotExist:
                pass

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
        except KeyError:
            return self.form_invalid(form)

        self.request.session[self.session_key] = questionnaire_step.slug
        return HttpResponseRedirect(redirect_to=questionnaire_step.get_absolute_url())
