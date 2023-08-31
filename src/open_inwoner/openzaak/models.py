from datetime import timedelta

from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from furl import furl
from solo.models import SingletonModel
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.managers import (
    UserCaseInfoObjectNotificationManager,
    UserCaseStatusNotificationManager,
    ZaakTypeConfigQueryset,
    ZaakTypeInformatieObjectTypeConfigQueryset,
)


def generate_default_file_extensions():
    return sorted(
        [
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "vsd",
            "png",
            "gif",
            "jpg",
            "tiff",
            "msg",
            "txt",
            "rtf",
            "jpeg",
            "bmp",
        ]
    )


class OpenZaakConfig(SingletonModel):
    """
    Global configuration and defaults for zaken and catalogi services.
    """

    zaak_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Open Zaak API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="+",
        blank=True,
        null=True,
    )
    zaak_max_confidentiality = models.CharField(
        max_length=32,
        choices=VertrouwelijkheidsAanduidingen.choices,
        default=VertrouwelijkheidsAanduidingen.openbaar,
        verbose_name=_("Case confidentiality"),
        help_text=_("Select maximum confidentiality level of cases"),
    )
    catalogi_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        related_name="+",
        blank=True,
        null=True,
    )
    document_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Documents API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="+",
        blank=True,
        null=True,
    )
    document_max_confidentiality = models.CharField(
        max_length=32,
        choices=VertrouwelijkheidsAanduidingen.choices,
        default=VertrouwelijkheidsAanduidingen.openbaar,
        verbose_name=_("Documents confidentiality"),
        help_text=_("Select confidentiality level of documents to display for cases"),
    )
    max_upload_size = models.PositiveIntegerField(
        verbose_name=_("Max upload file size (in MB)"),
        default=50,
        help_text=_("The max size of the file (in MB) which is uploaded."),
    )
    allowed_file_extensions = ArrayField(
        models.CharField(
            verbose_name=_("Allowed file extensions"),
            max_length=8,
        ),
        default=generate_default_file_extensions,
        help_text=_("A list of the allowed file extensions."),
    )
    form_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Form API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        blank=True,
        null=True,
    )

    skip_notification_statustype_informeren = models.BooleanField(
        verbose_name=_("Use StatusType.informeren workaround"),
        help_text=_(
            "Enable when StatusType.informeren is not supported by the ZGW backend. This requires ZaakTypeConfig's to be configured to determine on which changes to notify."
        ),
        default=False,
    )

    reformat_esuite_zaak_identificatie = models.BooleanField(
        verbose_name=_("Reformat eSuite Zaak.identificatie"),
        help_text=_(
            "Enable to reformat user-facing Zaak.identificatie numbers from internal eSuite format (ex: '0014ESUITE66392022') to user friendly format ('6639-2022')."
        ),
        default=False,
    )

    class Meta:
        verbose_name = _("Open Zaak configuration")


class CatalogusConfig(models.Model):
    url = models.URLField(
        verbose_name=_("Catalogus URL"),
        unique=True,
    )
    domein = models.CharField(
        verbose_name=_("Domein"),
        max_length=5,
    )
    rsin = models.CharField(
        verbose_name=_("RSIN"),
        max_length=9,
    )

    class Meta:
        ordering = ("domein", "rsin")

    def __str__(self):
        return f"{self.domein} - {self.rsin}"


class ZaakTypeConfig(models.Model):
    catalogus = models.ForeignKey(
        "openzaak.CatalogusConfig",
        on_delete=models.CASCADE,
        null=True,
    )

    identificatie = models.CharField(
        verbose_name=_("Zaaktype identificatie"),
        max_length=50,
    )
    omschrijving = models.CharField(
        verbose_name=_("Zaaktype omschrijving"),
        max_length=80,
        blank=True,
    )

    # actual config

    # notifications
    notify_status_changes = models.BooleanField(default=False)

    # documents
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        default="",
        help_text=_(
            "Description - clarification of why a user should upload a document for this case type"
        ),
    )
    external_document_upload_url = models.URLField(
        verbose_name=_("Document upload URL"),
        blank=True,
    )
    document_upload_enabled = models.BooleanField(
        verbose_name=_("Enable document upload via URL"),
        default=False,
    )

    # contact moments
    contact_form_enabled = models.BooleanField(
        verbose_name=_("Enable sending questions via OpenKlant API"),
        default=False,
    )

    objects = ZaakTypeConfigQueryset.as_manager()

    class Meta:
        verbose_name = _("Zaaktype Configuration")
        constraints = [
            UniqueConstraint(
                name="unique_identificatie_in_catalogus",
                fields=["catalogus", "identificatie"],
                condition=Q(catalogus__isnull=False),
            ),
            UniqueConstraint(
                name="unique_identificatie_without_catalogus",
                fields=["identificatie"],
                condition=Q(catalogus__isnull=True),
            ),
        ]

    @property
    def catalogus_url(self):
        if self.catalogus_id:
            return self.catalogus.url
        else:
            return None

    def __str__(self):
        bits = (
            self.identificatie,
            self.omschrijving,
        )
        return f" - ".join(b for b in bits if b)


class ZaakTypeInformatieObjectTypeConfig(models.Model):
    zaaktype_config = models.ForeignKey(
        "openzaak.ZaakTypeConfig",
        on_delete=models.CASCADE,
    )
    informatieobjecttype_url = models.URLField(
        verbose_name=_("Information object URL"),
        max_length=1000,
    )
    omschrijving = models.CharField(
        verbose_name=_("Omschrijving"),
        max_length=80,
    )
    zaaktype_uuids = ArrayField(
        models.UUIDField(
            verbose_name=_("Zaaktype UUID"),
        ),
        default=list,
    )

    # configuration

    document_upload_enabled = models.BooleanField(
        verbose_name=_("Enable document upload"),
        default=False,
    )
    document_notification_enabled = models.BooleanField(
        verbose_name=_("Enable document notifications"),
        default=False,
        help_text=_(
            "When enabled the user will receive a notification when a visible document is added to the case"
        ),
    )
    objects = ZaakTypeInformatieObjectTypeConfigQueryset.as_manager()

    class Meta:
        verbose_name = _("Zaaktype Information Object Configuration")

        constraints = [
            UniqueConstraint(
                name="unique_zaaktype_config_informatieobjecttype_url",
                fields=["zaaktype_config", "informatieobjecttype_url"],
            )
        ]

    def informatieobjecttype_uuid(self):
        if self.informatieobjecttype_url:
            segments = furl(self.informatieobjecttype_url).path.segments
            # grab uuid as last bit of url,
            # but handle trailing slash or weird urls from factories
            while segments:
                s = segments.pop()
                if s:
                    return s
            return self.informatieobjecttype_url
        return ""

    informatieobjecttype_uuid.short_description = _("Information object UUID")

    def __str__(self):
        return self.omschrijving


class UserCaseStatusNotification(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
    )
    case_uuid = models.UUIDField(
        verbose_name=_("Zaak UUID"),
    )
    status_uuid = models.UUIDField(
        verbose_name=_("Status UUID"),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"), default=timezone.now
    )

    objects = UserCaseStatusNotificationManager()

    class Meta:
        verbose_name = _("Open Zaak status notification record")

        constraints = [
            UniqueConstraint(
                name="unique_user_case_status",
                fields=["user", "case_uuid", "status_uuid"],
            )
        ]

    def has_received_similar_notes_within(self, delta: timedelta) -> bool:
        return (
            UserCaseStatusNotification.objects.filter(
                user=self.user,
                case_uuid=self.case_uuid,
                created_on__gte=timezone.now() - delta,
            )
            .exclude(id=self.id)
            .exists()
        )


class UserCaseInfoObjectNotification(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
    )
    case_uuid = models.UUIDField(
        verbose_name=_("Zaak UUID"),
    )
    zaak_info_object_uuid = models.UUIDField(
        verbose_name=_("InformatieObject UUID"),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"), default=timezone.now
    )

    objects = UserCaseInfoObjectNotificationManager()

    class Meta:
        verbose_name = _("Open Zaak info object notification record")

        constraints = [
            UniqueConstraint(
                name="unique_user_case_info_object",
                fields=["user", "case_uuid", "zaak_info_object_uuid"],
            )
        ]
