from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.db import IntegrityError, models, transaction

from open_inwoner.accounts.models import User

if TYPE_CHECKING:
    from open_inwoner.openzaak.models import (
        UserCaseInfoObjectNotification,
        UserCaseStatusNotification,
    )


class UserCaseStatusNotificationManager(models.Manager):
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


class UserCaseInfoObjectNotificationManager(models.Manager):
    def record_if_unique_notification(
        self,
        user: User,
        case_uuid: UUID,
        zaak_info_object_uuid: UUID,
    ) -> Optional["UserCaseInfoObjectNotification"]:
        """
        assume this is the first delivery but depend on the unique constraint
        """
        kwargs = {
            "user": user,
            "case_uuid": case_uuid,
            "zaak_info_object_uuid": zaak_info_object_uuid,
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


class ZaakTypeConfigQueryset(models.QuerySet):
    def get_visible_zt_configs_for_case_type_identification(
        self, case_type_identification
    ):
        """
        Returns all ZaakTypeConfig instances which allow external documents
        upload, have a url set and are based on a specific case type identificatie.
        """
        if not case_type_identification:
            return self.none()

        return self.filter(
            identificatie=case_type_identification,
            document_upload_enabled=True,
        ).exclude(external_document_upload_url="")
