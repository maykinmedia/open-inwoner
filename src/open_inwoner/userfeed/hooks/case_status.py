from datetime import timedelta

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, format_html
from django.utils.translation import gettext_lazy as _

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import Status, Zaak
from open_inwoner.openzaak.models import ZaakTypeStatusTypeConfig
from open_inwoner.openzaak.utils import translate_single_status
from open_inwoner.userfeed.adapter import FeedItem
from open_inwoner.userfeed.adapters import register_item_adapter
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.models import FeedItemData

STATUS_REUSE_TIME = timedelta(minutes=10)


def case_status_notification_received(user: User, case: Zaak, status: Status):
    data = {
        "case_uuid": case.uuid,
        "case_identificatie": case.identificatie,
        "case_omschrijving": case.omschrijving,
        "status_omschrijving": translate_single_status(
            status.statustype.statustekst or status.statustype.omschrijving
        ),
        # new for actionable
        "catalogus_url": case.zaaktype.catalogus,
        "case_type_identificatie": case.zaaktype.identificatie,
        "status_type_url": status.statustype.url,
    }

    action_required = False
    status_config = ZaakTypeStatusTypeConfig.objects.find_for(case, status)
    if status_config:
        action_required = status_config.action_required

    # let's try to update last record if change happened recently
    qs = FeedItemData.objects.filter(
        user=user,
        type=FeedItemType.case_status_changed,
        ref_uuid=case.uuid,
    )
    qs = qs.filter(Q(display_at__gte=timezone.now() - STATUS_REUSE_TIME))

    # try update as notifications can be delivered multiple times
    if not qs.update(
        display_at=timezone.now(),
        completed_at=None,
        type_data=data,
        action_required=action_required,
    ):
        FeedItemData.objects.create(
            user=user,
            type=FeedItemType.case_status_changed,
            ref_uuid=case.uuid,
            type_data=data,
            action_required=action_required,
        )


def case_status_seen(user: User, case: Zaak):
    FeedItemData.objects.mark_uuid_completed(
        user, FeedItemType.case_status_changed, case.uuid
    )


class CaseStatusUpdateFeedItem(FeedItem):
    base_title = _("Case status update")
    base_message = _("Case status has been changed to '{status}'")

    cms_apps = ["cases"]

    status_config: ZaakTypeStatusTypeConfig | None = None

    def __init__(self, data: FeedItemData):
        super().__init__(data)

        self.status_config = ZaakTypeStatusTypeConfig.objects.find_for_types_from_str(
            self.get_data("catalogus_url"),
            self.get_data("case_type_identificatie"),
            self.get_data("status_type_url"),
        )

    @property
    def title(self) -> str:
        return self.get_data("case_omschrijving", super().title)

    @property
    def message(self) -> str:
        status_text = self.get_data("status_omschrijving")
        status_text = translate_single_status(status_text)
        html = escape(self.base_message)
        status = format_html('<span class="status">{}</span>', status_text)
        html = format_html(html, status=status)

        return html

    @property
    def action_url(self) -> str:
        uuid = self.get_data("case_uuid")
        return reverse("cases:case_detail", kwargs={"object_id": uuid})

    @property
    def status_text(self) -> str:
        if self.status_config and self.status_config.status_indicator_text:
            return self.status_config.status_indicator_text
        else:
            return super().status_text

    @property
    def status_indicator(self) -> str:
        if self.status_config and self.status_config.status_indicator:
            return self.status_config.status_indicator
        else:
            return super().status_indicator


register_item_adapter(CaseStatusUpdateFeedItem, FeedItemType.case_status_changed)
