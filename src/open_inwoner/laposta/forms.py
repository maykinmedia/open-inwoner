import logging

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ipware import get_client_ip
from requests.exceptions import RequestException

from open_inwoner.laposta.api_models import UserData
from open_inwoner.laposta.models import LapostaConfig, Subscription
from open_inwoner.utils.api import ClientError

from .choices import get_list_choices
from .client import create_laposta_client

logger = logging.getLogger(__name__)


class NewsletterSubscriptionForm(forms.Form):
    newsletters = forms.MultipleChoiceField(
        label=_("Nieuwsbrieven"),
        required=False,
        widget=forms.widgets.CheckboxSelectMultiple,
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(**kwargs)

        if laposta_client := create_laposta_client():
            lists = laposta_client.get_lists()
            self.fields["newsletters"].choices = get_list_choices(lists)
            if limited_to := LapostaConfig.get_solo().limit_list_selection_to:
                self.fields["newsletters"].choices = [
                    choice
                    for choice in self.fields["newsletters"].choices
                    if choice[0] in limited_to
                ]

            self.fields["newsletters"].initial = [
                subscription.list_id
                for subscription in Subscription.objects.filter(user=user)
            ]

    def save(self, request, *args, **kwargs):
        newsletters = self.cleaned_data["newsletters"]

        client = create_laposta_client()
        if not client:
            return

        list_name_mapping = dict(self.fields["newsletters"].choices)
        user_data = UserData(
            ip=get_client_ip(request)[0],
            email=request.user.email,
            source_url=None,
            custom_fields=None,
            options=None,
        )
        existing_subscriptions = set(
            Subscription.objects.filter(user=request.user).values_list(
                "list_id", flat=True
            )
        )

        to_create = []
        for list_id in newsletters:
            if list_id in existing_subscriptions:
                continue

            try:
                member = client.create_subscription(list_id, user_data)
            except (RequestException, ClientError):
                logger.exception(
                    "Something went wrong while trying to create subscription"
                )
                self.add_error(
                    "newsletters",
                    ValidationError(
                        _(
                            "Something went wrong while trying to subscribe "
                            "to '{list_name}', please try again later"
                        ).format(list_name=list_name_mapping[list_id])
                    ),
                )
            else:
                if member:
                    to_create.append(
                        Subscription(
                            list_id=member.list_id,
                            member_id=member.member_id,
                            user=request.user,
                        )
                    )

        if to_create:
            Subscription.objects.bulk_create(to_create)

        unsubscribe_from_ids = existing_subscriptions - set(newsletters)
        unsubscribe_from = Subscription.objects.filter(
            user=request.user, list_id__in=unsubscribe_from_ids
        )

        to_delete_ids = []
        for subscription in unsubscribe_from:
            try:
                client.remove_subscription(subscription.list_id, subscription.member_id)
            except (RequestException, ClientError):
                logger.exception(
                    "Something went wrong while trying to create subscription"
                )
                self.add_error(
                    "newsletters",
                    ValidationError(
                        _(
                            "Something went wrong while trying to unsubscribe "
                            "from '{list_name}', please try again later"
                        ).format(list_name=list_name_mapping[subscription.list_id])
                    ),
                )
            else:
                to_delete_ids.append(subscription.list_id)
        Subscription.objects.filter(
            user=request.user, list_id__in=to_delete_ids
        ).delete()
