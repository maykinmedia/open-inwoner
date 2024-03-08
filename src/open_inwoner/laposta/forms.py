from django import forms
from django.utils.translation import gettext_lazy as _

from .client import create_laposta_client


class NewsletterSubscriptionForm(forms.Form):
    newsletters = forms.MultipleChoiceField(
        label=_("Nieuwsbrieven"),
        required=False,
        widget=forms.widgets.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        # TODO fetch subscriptions for current user and preselect those
        if laposta_client := create_laposta_client():
            lists = laposta_client.get_lists()
            self.fields["newsletters"].choices = [
                (laposta_list.list_id, f"{laposta_list.name}: {laposta_list.remarks}")
                for laposta_list in lists
                if laposta_list.name
            ]

    def save(self, *args, **kwargs):
        # TODO create subscriptions
        pass
