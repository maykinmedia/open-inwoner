from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.db import IntegrityError, models, transaction

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import Zaak, ZaakType

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
    def filter_catalogus(self, case_type: ZaakType):
        if case_type.catalogus:
            # support both url and resolved dataclass
            catalogus_url = (
                case_type.catalogus
                if isinstance(case_type.catalogus, str)
                else case_type.catalogus.url
            )
            return self.filter(
                zaaktype_config__catalogus__url=catalogus_url,
            )
        else:
            return self.filter(
                zaaktype_config__catalogus__isnull=True,
            )

    def filter_case_type(self, case_type: ZaakType):
        return self.filter_catalogus(case_type).filter(
            zaaktype_uuids__contains=[case_type.uuid],
            zaaktype_config__identificatie=case_type.identificatie,
        )

    def filter_enabled_for_case_type(self, case_type: ZaakType):
        """
        Returns all ZaakTypeInformatieObjectTypeConfig instances which allow
        documents upload and are based on a specific case and case type.
        """
        if not case_type:
            return self.none()

        return self.filter_case_type(case_type).filter(
            document_upload_enabled=True,
        )

    def get_for_case_and_info_type(
        self, case_type: ZaakType, info_object_type_url: str
    ):
        return self.filter_case_type(case_type).get(
            informatieobjecttype_url=info_object_type_url,
        )


class ZaakTypeConfigQueryset(models.QuerySet):
    def filter_catalogus(self, case_type: ZaakType):
        if case_type.catalogus:
            # support both url and resolved dataclass
            catalogus_url = (
                case_type.catalogus
                if isinstance(case_type.catalogus, str)
                else case_type.catalogus.url
            )
            return self.filter(
                catalogus__url=catalogus_url,
            )
        else:
            return self.filter(
                catalogus__isnull=True,
            )

    def filter_case_type(self, case_type: ZaakType):
        return self.filter_catalogus(case_type).filter(
            identificatie=case_type.identificatie,
        )

    def filter_enabled_for_case_type(self, case_type: ZaakType):
        """
        Returns all ZaakTypeConfig instances which allow external documents
        upload, have a url set and are based on a specific case type identificatie.
        """
        if not case_type:
            return self.none()

        return (
            self.filter_case_type(case_type)
            .filter(
                document_upload_enabled=True,
            )
            .exclude(external_document_upload_url="")
        )

    def filter_questions_enabled_for_case_type(self, case_type: ZaakType):
        """
        Returns all ZaakTypeConfig instances which allow questions via OpenKlant API.
        """
        if not case_type:
            return self.none()

        return self.filter_case_type(case_type).filter(questions_enabled=True)
