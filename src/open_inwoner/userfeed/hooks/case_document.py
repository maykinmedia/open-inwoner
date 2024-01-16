from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import Zaak, ZaakInformatieObject
from open_inwoner.userfeed.adapter import FeedItem
from open_inwoner.userfeed.adapters import register_item_adapter
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.models import FeedItemData


def case_document_added_notification_received(
    user: User, case: Zaak, case_info_object: ZaakInformatieObject
):
    data = {
        "case_uuid": case.uuid,
        "case_identificatie": case.identificatie,
        "case_omschrijving": case.omschrijving,
        "case_info_object_uuid": case_info_object.uuid,
        "case_info_object_titel": case_info_object.titel,
        "info_object_uuid": case_info_object.informatieobject.uuid,
        "info_object_titel": case_info_object.informatieobject.titel,
    }

    # use a ref_key to de-duplicate per info object
    ref_key = str(case_info_object.uuid)

    qs = FeedItemData.objects.filter(
        user=user,
        type=FeedItemType.case_document_added,
        ref_uuid=case.uuid,
        ref_key=ref_key,
    )

    # try update as notifications can be delivered multiple times
    if not qs.update(
        display_at=timezone.now(),
        completed_at=None,
        type_data=data,
    ):
        FeedItemData.objects.create(
            user=user,
            type=FeedItemType.case_document_added,
            ref_uuid=case.uuid,
            ref_key=ref_key,
            type_data=data,
        )


def case_documents_seen(user: User, case: Zaak):
    # mark all document items for this case as completed
    FeedItemData.objects.mark_uuid_completed(
        user, FeedItemType.case_document_added, case.uuid
    )


class CaseDocumentAddedFeedItem(FeedItem):
    base_title = _("Case document added")
    base_message = _("Case document '{title}' has been added")

    cms_apps = ["cases"]

    @property
    def title(self) -> str:
        return self.get_data("case_omschrijving", super().title)

    @property
    def message(self) -> str:
        title = (
            self.get_data("info_object_titel")
            or self.get_data("case_info_object_titel")
            or _("onbekend")
        )
        return self.base_message.format(title=title)

    @property
    def action_url(self) -> str:
        uuid = self.get_data("case_uuid")
        return reverse("cases:case_detail", kwargs={"object_id": uuid})


register_item_adapter(CaseDocumentAddedFeedItem, FeedItemType.case_document_added)
