import logging

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ipware import get_client_ip
from requests.exceptions import RequestException

from open_inwoner.laposta.api_models import UserData
from open_inwoner.laposta.models import LapostaConfig
from open_inwoner.utils.api import ClientError

from ..accounts.models import User
from .choices import get_list_choices, get_list_remarks_mapping
from .client import create_laposta_client

logger = logging.getLogger(__name__)


class NewsletterSubscriptionForm(forms.Form):
    newsletters = forms.MultipleChoiceField(
        label=_("Nieuwsbrieven"),
        required=False,
        widget=forms.widgets.CheckboxSelectMultiple,
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(**kwargs)

        if not request.user.has_verified_email():
            return

        if laposta_client := create_laposta_client():
            lists = laposta_client.get_lists()
            self.fields["newsletters"].choices = get_list_choices(lists)
            self.fields["newsletters"].remarks_mapping = get_list_remarks_mapping(lists)
            if limited_to := LapostaConfig.get_solo().limit_list_selection_to:
                self.fields["newsletters"].choices = [
                    choice
                    for choice in self.fields["newsletters"].choices
                    if choice[0] in limited_to
                ]

            # In case of errors, we want to keep the same data selected
            if "newsletters" in request.POST:
                initial_data = request.POST.getlist("newsletters")
            else:
                initial_data = laposta_client.get_subscriptions_for_email(
                    limited_to, request.user.verified_email
                )

            self.fields["newsletters"].initial = initial_data

    def save(self, request, *args, **kwargs):
        user: User = request.user
        if not user.has_verified_email():
            return

        client = create_laposta_client()
        if not client:
            return

        newsletters = self.cleaned_data["newsletters"]
        has_errors = False

        list_name_mapping = dict(self.fields["newsletters"].choices)
        user_data = UserData(
            ip=get_client_ip(request)[0],
            email=user.verified_email,
            source_url=None,
            custom_fields={"toestemming": "Ja, ik wil de nieuwsbrief ontvangen"},
            options=None,
        )
        limited_to = LapostaConfig.get_solo().limit_list_selection_to
        existing_subscriptions = set(
            client.get_subscriptions_for_email(limited_to, user.verified_email)
        )
        for list_id in newsletters:
            if list_id in existing_subscriptions:
                continue

            try:
                client.create_subscription(list_id, user_data)
            except (RequestException, ClientError):
                logger.exception(
                    "Something went wrong while trying to create subscription"
                )
                has_errors = True
                self.add_error(
                    "newsletters",
                    ValidationError(
                        _(
                            "Something went wrong while trying to subscribe "
                            "to '{list_name}', please try again later"
                        ).format(list_name=list_name_mapping[list_id])
                    ),
                )

        unsubscribe_from_ids = existing_subscriptions - set(newsletters)
        for list_id in unsubscribe_from_ids:
            try:
                client.remove_subscription(list_id, user.verified_email)
            except (RequestException, ClientError):
                logger.exception(
                    "Something went wrong while trying to delete subscription"
                )
                has_errors = True
                self.add_error(
                    "newsletters",
                    ValidationError(
                        _(
                            "Something went wrong while trying to unsubscribe "
                            "from '{list_name}', please try again later"
                        ).format(list_name=list_name_mapping[list_id])
                    ),
                )

        if has_errors:
            messages.warning(
                request, _("Er ging iets mis bij het opslaan van je voorkeuren")
            )
