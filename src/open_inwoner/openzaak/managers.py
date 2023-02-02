from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.db import IntegrityError, models, transaction

from open_inwoner.accounts.models import User

if TYPE_CHECKING:
    from open_inwoner.openzaak.models import UserCaseStatusNotification


class UserCaseStatusNotificationQueryset(models.QuerySet):
    def get_user_case_notifications(self, user, case_uuid):
        return self.filter(user=user, case_uuid=case_uuid)

    def has_notification(self, user, case_uuid, status_uuid):
        return self.filter(
            user=user, case_uuid=case_uuid, status_uuid=status_uuid
        ).exists()


class UserCaseStatusNotificationManager(
    models.Manager.from_queryset(UserCaseStatusNotificationQueryset)
):
    def record_if_unique_notification(
        self,
        user: User,
        case_uuid: UUID,
        status_uuid: UUID,
    ) -> Optional["UserCaseStatusNotification"]:
        """
        assume this is the first delivery but depend on the unique constraint
        """
        kwargs = {
            "user": user,
            "case_uuid": case_uuid,
            "status_uuid": status_uuid,
        }
        try:
            with transaction.atomic():
                note = self.create(**kwargs)
                return note
        except IntegrityError:
            return None


class ZaakTypeInformatieObjectTypeConfigQueryset(models.QuerySet):
    def get_visible_ztiot_configs_for_case(self, case):
        """
        Returns all ZaakTypeInformatieObjectTypeConfig instances which allow
        documents upload and are based on a specific case and case type.
        """
        if not case:
            return self.none()

        return self.filter(
            zaaktype_uuids__contains=[case.zaaktype.uuid],
            zaaktype_config__identificatie=case.zaaktype.identificatie,
            document_upload_enabled=True,
        )
