from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .choices import get_list_choices
from .client import create_laposta_client
from .models import LapostaConfig, Subscription


class LapostaConfigForm(forms.ModelForm):
    limit_list_selection_to = forms.MultipleChoiceField(
        widget=forms.widgets.CheckboxSelectMultiple(), required=False
    )

    class Meta:
        model = LapostaConfig
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "limit_list_selection_to"
        ].help_text = self.Meta.model.limit_list_selection_to.field.help_text

        if client := create_laposta_client():
            lists = client.get_lists()
            self.fields["limit_list_selection_to"].choices = get_list_choices(lists)


@admin.register(LapostaConfig)
class LapostaConfigAdmin(SingletonModelAdmin):
    form = LapostaConfigForm
    fieldsets = (
        (
            _("Basic"),
            {
                "fields": (
                    "api_root",
                    "basic_auth_username",
                    "basic_auth_password",
                ),
            },
        ),
        (
            _("Advanced"),
            {"fields": ("limit_list_selection_to",)},
        ),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["list_id", "user", "member_id"]
    list_filter = ["list_id", "user"]
    search_fields = ("user__first_name", "user__last_name", "user__email")
