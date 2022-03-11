from django import forms

from .models import Plan


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("title", "end_date", "contacts")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        extended_contacts = user.get_extended_active_contacts()
        self.fields["contacts"].queryset = extended_contacts
        self.fields["contacts"].choices = [
            [c.id, f"{c.other_user_first_name} {c.other_user_last_name}"]
            for c in extended_contacts
        ]

    def save(self, user, commit=True):
        if not self.instance.pk:
            self.instance.created_by = user
        return super().save(commit=commit)


class PlanGoalForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("goal",)

    def save(self, commit=True):
        return super().save(commit=commit)
