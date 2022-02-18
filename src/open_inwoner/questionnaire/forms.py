from django import forms
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
