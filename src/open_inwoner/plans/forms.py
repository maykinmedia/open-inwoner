from datetime import timedelta
from io import BytesIO

from django import forms
from django.core.files.base import File
from django.utils import timezone
from django.utils.translation import gettext as _

from open_inwoner.accounts.models import Action, Document

from .models import Plan, PlanTemplate


class PlanForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=PlanTemplate.objects.all(),
        required=False,
        empty_label=_("No template"),
        widget=forms.widgets.RadioSelect(),
    )

    class Meta:
        model = Plan
        fields = ("title", "end_date", "contacts", "template")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        extended_contacts = user.get_extended_active_contacts()
        self.fields["contacts"].queryset = extended_contacts
        self.fields["contacts"].choices = [
            [c.id, f"{c.other_user_first_name} {c.other_user_last_name}"]
            for c in extended_contacts
        ]

        if self.instance.pk:
            del self.fields["template"]

    def save(self, user, commit=True):
        if not self.instance.pk:
            self.instance.created_by = user

        plan = super().save(commit=commit)

        template = self.cleaned_data.get("template")
        if template:
            self.instance.goal = template.goal
            self.instance.save()

            if template.file:
                template.file.file.seek(0)
                template_file = File(
                    BytesIO(template.file.file.read()), template.file.original_filename
                )
                Document.objects.create(
                    name=template.file.name,
                    file=template_file,
                    owner=user,
                    plan=plan,
                )

            now = timezone.now()
            for action_template in template.actiontemplates.all():
                end_date = now + timedelta(days=action_template.end_in_days)
                Action.objects.create(
                    name=action_template.name,
                    description=action_template.description,
                    goal=action_template.goal,
                    type=action_template.type,
                    end_date=end_date.date(),
                    is_for=user,
                    created_by=user,
                    plan=plan,
                )
        return plan


class PlanGoalForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("goal",)

    def save(self, commit=True):
        return super().save(commit=commit)
