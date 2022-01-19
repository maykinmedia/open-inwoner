from django import forms

from .models import Plan


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("title", "end_date", "contacts")

    def save(self, user, commit=True):
        self.instance.created_by = user
        return super().save(commit=commit)


class PlanGoalForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("goal",)

    def save(self, user, commit=True):
        return super().save(commit=commit)
