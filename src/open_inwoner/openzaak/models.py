from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.managers import UserCaseStatusNotificationManager


def generate_default_file_extensions():
    return [
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
        null=True,
    )
    document_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Documents API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="+",
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

    skip_notication_statustype_informeren = models.BooleanField(
        verbose_name=_("Use StatusType.informeren workaround"),
        help_text=_(
            "Enable when StatusType.informeren is not supported by the ZGW backend. This requires ZaakTypeConfig's to be configured to determine on which changes to notify."
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
    )

    identificatie = models.CharField(
        verbose_name=_("Zaaktype identificatie"),
        max_length=50,
        # TODO we probably want this index
        # db_index=True
    )
    omschrijving = models.CharField(
        verbose_name=_("Zaaktype omschrijving"),
        max_length=80,
        blank=True,
    )

    # actual config
    notify_status_changes = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Zaaktype Configuration")
        constraints = [
            UniqueConstraint(
                fields=["catalogus", "identificatie"],
                name="unique_catalogus_identificatie",
            )
        ]

    def __str__(self):
        bits = (
            self.identificatie,
            self.omschrijving,
        )
        return f" - ".join(b for b in bits if b)


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
    created = models.DateTimeField(verbose_name=_("Created"), default=timezone.now)

    objects = UserCaseStatusNotificationManager()

    class Meta:
        verbose_name = _("Open Zaak notification user inform record")

        constraints = [
            UniqueConstraint(
                name="unique_user_case_status",
                fields=["user", "case_uuid", "status_uuid"],
            )
        ]
