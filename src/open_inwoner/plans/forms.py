from django import forms

from .models import Plan


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("title", "end_date", "contacts")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contacts"].queryset = user.contacts.all()

    def save(self, user, commit=True):
        self.instance.created_by = user
        return super().save(commit=commit)


class PlanGoalForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("goal",)

    def save(self, commit=True):
        return super().save(commit=commit)
