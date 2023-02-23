from datetime import timedelta
from io import BytesIO

from django import forms
from django.core.files.base import File
from django.utils import timezone
from django.utils.translation import gettext as _

from open_inwoner.accounts.models import Action, Document, User

from .choices import PlanStatusChoices
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
        fields = ("title", "end_date", "plan_contacts", "template")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        user_contacts = self.user.get_active_contacts()
        self.fields["plan_contacts"].queryset = user_contacts

        # NOTE we have to convert the ID value of the choice to string to make components recognize checked (taiga 899)
        self.fields["plan_contacts"].choices = [
            [str(c.id), c.get_full_name()] for c in user_contacts
        ]
        self.fields["template"].choices = [
            (str(t.id), t) for t in self.fields["template"].queryset
        ]

        if self.instance.pk:
            del self.fields["template"]

    def clean_plan_contacts(self):
        # Make sure current user exists in plan_contacts when editing form
        data = self.cleaned_data["plan_contacts"]
        if self.instance.pk:
            data |= User.objects.filter(pk=self.user.pk)
        return data.distinct()

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


class PlanListFilterForm(forms.ModelForm):
    plan_contacts = forms.ModelChoiceField(
        queryset=Plan.objects.none(), required=False, to_field_name="uuid"
    )
    status = forms.ChoiceField(
        label=_("Status"), choices=PlanStatusChoices.choices, required=False
    )
    query = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Zoeken")}),
    )

    class Meta:
        model = Plan
        fields = ("plan_contacts", "status")

    def __init__(self, available_contacts, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["plan_contacts"].queryset = available_contacts
        self.fields["plan_contacts"].choices = [
            [str(c.uuid), c.get_full_name()] for c in available_contacts
        ]

        # we have to add the empty label since we defined choices above
        self.fields["plan_contacts"].choices.insert(0, ("", _("Contactpersoon")))
