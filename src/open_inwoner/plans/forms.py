from datetime import date, timedelta
from io import BytesIO
from typing import Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.utils import formats, timezone
from django.utils.translation import gettext as _

from open_inwoner.accounts.models import Action, Document, User

from .choices import PlanStatusChoices
from .models import Plan, PlanTemplate


class PlanTemplateChoiceForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=PlanTemplate.objects.all(),
        required=True,
        empty_label=_("No template"),
        widget=forms.widgets.HiddenInput(),  # Form is used for validation only
    )


class CreatePlanFromTemplateForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = (
            "end_date",
            "plan_contacts",
        )

    def __init__(self, user, template, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        self.template = template
        user_contacts = self.user.get_active_contacts()
        self.fields["plan_contacts"].queryset = user_contacts

        # NOTE we have to convert the ID value of the choice to string to make components recognize checked (taiga 899)
        self.fields["plan_contacts"].choices = [
            [str(c.id), c.get_full_name() or c.email] for c in user_contacts
        ]

    def clean_plan_contacts(self):
        # Make sure current user exists in plan_contacts when editing form
        data = self.cleaned_data["plan_contacts"]
        if self.instance.pk:
            data |= User.objects.filter(pk=self.user.pk)
        return data.distinct()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if (end_date := cleaned_data.get("end_date")) and (
            actiontemplates := self.template.actiontemplates.all()
        ):
            latest_end_in_days = max([a.end_in_days for a in actiontemplates])

            today = date.today()
            actions_end_date = today + timedelta(days=latest_end_in_days)

            if end_date < actions_end_date:
                self.add_error(
                    "end_date",
                    _(
                        "The end date of the plan cannot precede the end dates of the "
                        "actions in the selected template. The earliest possible end date "
                        "for this type of plan is %s."
                    )
                    % formats.date_format(actions_end_date, use_l10n=True),
                )

        return cleaned_data

    def save(self, user, commit=True):
        instance = cast(Plan, self.instance)
        if not instance.pk:
            instance.created_by = user

        # Ensure we have a primary key to setup relations below
        super().save(commit=commit)

        instance.title = self.template.name
        instance.goal = self.template.goal
        instance.description = self.template.description
        if self.template.file:
            self.template.file.file.seek(0)
            template_file = File(
                BytesIO(self.template.file.file.read()),
                self.template.file.original_filename,
            )
            Document.objects.create(
                name=self.template.file.name,
                file=template_file,
                owner=user,
                plan=instance,
            )

        now = timezone.now()
        for action_template in self.template.actiontemplates.all():
            end_date = now + timedelta(days=action_template.end_in_days)
            Action.objects.create(
                name=action_template.name,
                description=action_template.description,
                type=action_template.type,
                end_date=end_date.date(),
                is_for=user,
                created_by=user,
                plan=self.instance,
            )

        instance.save()
        return instance


class PlanForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=PlanTemplate.objects.all(),
        required=False,
        empty_label=_("No template"),
        widget=forms.widgets.RadioSelect(),
    )

    class Meta:
        model = Plan
        fields = (
            "title",
            "goal",
            "description",
            "end_date",
            "plan_contacts",
        )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        user_contacts = self.user.get_active_contacts()
        self.fields["plan_contacts"].queryset = user_contacts

        # NOTE we have to convert the ID value of the choice to string to make components recognize checked (taiga 899)
        self.fields["plan_contacts"].choices = [
            [str(c.id), c.get_full_name()] for c in user_contacts
        ]

    def clean(self):
        cleaned_data = super().clean()

        goal = cleaned_data.get("goal")
        plan_contacts = cleaned_data.get("plan_contacts")
        end_date = cleaned_data.get("end_date")

        if not plan_contacts or (
            plan_contacts and not plan_contacts.exclude(pk=self.user.pk)
        ):
            raise ValidationError(
                _("At least one collaborator is required for a plan.")
            )

    def clean_plan_contacts(self):
        # Make sure current user exists in plan_contacts when editing form
        data = self.cleaned_data["plan_contacts"]
        if self.instance.pk:
            data |= User.objects.filter(pk=self.user.pk)
        return data.distinct()

    def save(self, user, commit=True):
        if not self.instance.pk:
            self.instance.created_by = user

        return super().save(commit=commit)


class PlanGoalForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = (
            "goal",
            "description",
        )

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
        fields = (
            "plan_contacts",
            "status",
        )

    def __init__(self, available_contacts, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["plan_contacts"].queryset = available_contacts
        self.fields["plan_contacts"].choices = [
            [str(c.uuid), c.get_full_name()] for c in available_contacts
        ]

        # we have to add the empty label since we defined choices above
        self.fields["plan_contacts"].choices.insert(0, ("", _("Contactpersoon")))
