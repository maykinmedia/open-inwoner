from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from django.db import IntegrityError, models, transaction
from django.utils import timezone

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import Status, StatusType, Zaak, ZaakType
from open_inwoner.utils.translate import TranslationLookup

if TYPE_CHECKING:
    from open_inwoner.openzaak.models import (
        UserCaseInfoObjectNotification,
        UserCaseStatusNotification,
    )


class UserCaseNotificationBaseManager(models.Manager):
    def has_received_similar_notes_within(
        self,
        user: User,
        case_uuid,
        delta: timedelta,
        collision_key: str,
        not_record_id: int | None = None,
    ) -> bool:
        qs = self.filter(
            user=user,
            case_uuid=case_uuid,
            created_on__gte=timezone.now() - delta,
            is_sent=True,
            collision_key=collision_key,
        )
        if not_record_id:
            qs = qs.exclude(id=not_record_id)
        return qs.exists()

    def attempt_create(self, **kwargs):
        try:
            with transaction.atomic():
                return self.create(**kwargs)
        except IntegrityError:
            return None


class UserCaseStatusNotificationManager(UserCaseNotificationBaseManager):
    def record_if_unique_notification(
        self,
        user: User,
        case_uuid: UUID,
        status_uuid: UUID,
        collision_key: str,
    ) -> "UserCaseStatusNotification | None":
        """
        assume this is the first delivery but depend on the unique constraint
        """
        kwargs = {
            "user": user,
            "case_uuid": case_uuid,
            "status_uuid": status_uuid,
            "collision_key": collision_key,
        }
        return self.attempt_create(**kwargs)


class UserCaseInfoObjectNotificationManager(UserCaseNotificationBaseManager):
    def record_if_unique_notification(
        self,
        user: User,
        case_uuid: UUID,
        zaak_info_object_uuid: UUID,
        collision_key: str,
    ) -> "UserCaseInfoObjectNotification | None":
        """
        assume this is the first delivery but depend on the unique constraint
        """
        kwargs = {
            "user": user,
            "case_uuid": case_uuid,
            "zaak_info_object_uuid": zaak_info_object_uuid,
            "collision_key": collision_key,
        }
        return self.attempt_create(**kwargs)


class CatalogusConfigManager(models.Manager):
    def get_by_natural_key(self, url):
        return self.get(url=url)


class ZaakTypeInformatieObjectTypeConfigQueryset(models.QuerySet):
    def get_by_natural_key(
        self,
        informatieobjecttype_url,
        zaak_type_config_identificatie,
        catalogus_url,
    ):
        from .models import ZaakTypeConfig

        return self.get(
            zaaktype_config=ZaakTypeConfig.objects.get(
                identificatie=zaak_type_config_identificatie,
                catalogus__url=catalogus_url,
            ),
            informatieobjecttype_url=informatieobjecttype_url,
        )

    def filter_catalogus(self, case_type: ZaakType):
        # support both url and resolved dataclass
        catalogus_url = (
            case_type.catalogus
            if isinstance(case_type.catalogus, str)
            else case_type.catalogus.url
        )
        return self.filter(
            zaaktype_config__catalogus__url=catalogus_url,
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
    def get_by_natural_key(
        self,
        identificatie,
        catalogus_url,
    ):
        return self.get(
            identificatie=identificatie,
            catalogus__url=catalogus_url,
        )

    def filter_catalogus(self, case_type: ZaakType):
        # support both url and resolved dataclass
        catalogus_url = (
            case_type.catalogus
            if isinstance(case_type.catalogus, str)
            else case_type.catalogus.url
        )
        return self.filter(
            catalogus__url=catalogus_url,
        )

    def filter_case_type(self, case_type: ZaakType):
        return self.filter_catalogus(case_type).filter(
            identificatie=case_type.identificatie,
        )

    def filter_from_str(self, catalogus_url: str, case_type_identificatie: str):
        return self.filter(
            catalogus__url=catalogus_url,
            identificatie=case_type_identificatie,
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


class ZaakTypeStatusTypeConfigQuerySet(models.QuerySet):
    def get_by_natural_key(
        self,
        statustype_url,
        zaak_type_config_identificatie,
        catalogus_url,
    ):
        from .models import ZaakTypeConfig

        return self.get(
            zaaktype_config=ZaakTypeConfig.objects.get(
                identificatie=zaak_type_config_identificatie,
                catalogus__url=catalogus_url,
            ),
            statustype_url=statustype_url,
        )

    def find_for(self, case: Zaak, status: Status):
        return self.find_for_types(case.zaaktype, status.statustype)

    def find_for_types(self, case_type: ZaakType, status_type: StatusType):
        from .models import ZaakTypeConfig

        ztc = ZaakTypeConfig.objects.filter_case_type(case_type)
        return self.filter(
            zaaktype_config__in=ztc, statustype_url=status_type.url
        ).first()

    def find_for_types_from_str(
        self, catalogus_url: str, case_type_identificatie: str, status_type_url: str
    ):
        from .models import ZaakTypeConfig

        ztc = ZaakTypeConfig.objects.filter_from_str(
            catalogus_url, case_type_identificatie
        )
        return self.filter(
            zaaktype_config__in=ztc, statustype_url=status_type_url
        ).first()


class ZaakTypeResultaatTypeConfigManger(models.Manager):
    def get_by_natural_key(
        self,
        resultaattype_url,
        zaak_type_config_identificatie,
        catalogus_url,
    ):
        from .models import ZaakTypeConfig

        return self.get(
            zaaktype_config=ZaakTypeConfig.objects.get(
                identificatie=zaak_type_config_identificatie,
                catalogus__url=catalogus_url,
            ),
            resultaattype_url=resultaattype_url,
        )


class StatusTranslationQuerySet(models.QuerySet):
    def get_lookup(self):
        return TranslationLookup(self.values_list("status", "translation"))
