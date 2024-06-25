import warnings
from datetime import timedelta

from django.db import models, transaction
from django.db.models import Q, UniqueConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField
from furl import furl
from solo.models import SingletonModel
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.managers import (
    UserCaseInfoObjectNotificationManager,
    UserCaseStatusNotificationManager,
    ZaakTypeConfigQueryset,
    ZaakTypeInformatieObjectTypeConfigQueryset,
    ZaakTypeStatusTypeConfigQuerySet,
)

from .constants import StatusIndicators


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


class ZGWApiGroupConfig(models.Model):
    """A set of of ZGW service configurations."""

    open_zaak_config = models.ForeignKey(
        "openzaak.OpenZaakConfig", on_delete=models.PROTECT, related_name="api_groups"
    )

    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this set of ZGW APIs."),
    )
    zrc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Zaken API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="zgwset_zrc_config",
        null=True,
    )
    drc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="zgwset_drc_config",
        null=True,
    )
    ztc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        related_name="zgwset_ztc_config",
        null=True,
    )
    form_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Form API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="zgwset_orc_form_config",
        null=True,
    )

    class Meta:
        verbose_name = _("ZGW API set")
        verbose_name_plural = _("ZGW API sets")

    def __str__(self):
        return self.name


# This will help us track legacy invocations of the root-level service config
_default_zgw_api_group_deprecation_message = (
    "This usage of `default_zgw_api_group` should be refactored to "
    "support multiple ZGW backends"
)

warnings.filterwarnings(
    "once", _default_zgw_api_group_deprecation_message, category=DeprecationWarning
)


class OpenZaakConfig(SingletonModel):
    """
    Global configuration and defaults for zaken and catalogi services.
    """

    @property
    def default_zgw_api_group(self):
        # TODO: This is a temporary solution to the new mult-backend
        # ZGW configuration to avoid breaking the existing API.
        # The *_service fields are proxied through this field to
        # avoid having two sources of truth regarding the configured
        # ZGW services. The legacy code will simply have a single
        # backend configured and retrieve this through the proxy.

        if (api_groups_count := self.api_groups.count()) == 0:
            return None

        if api_groups_count > 0:
            warnings.warn(
                _default_zgw_api_group_deprecation_message,
                DeprecationWarning,
            )

            return self.api_groups.first()

    def _set_zgw_service(self, field: str, service):
        if self.pk is None:
            raise ValueError(
                f"Please save your {self.__class__} instance before setting services"
            )

        with transaction.atomic():
            if self.default_zgw_api_group is None:
                ZGWApiGroupConfig.objects.create(open_zaak_config=self)

            default_group = self.default_zgw_api_group
            setattr(default_group, field, service)
            default_group.save()

            return getattr(default_group, field)

    @property
    def zaak_service(self):
        if self.default_zgw_api_group is None:
            return None

        return self.default_zgw_api_group.zrc_service

    @zaak_service.setter
    def zaak_service(self, service):
        return self._set_zgw_service("zrc_service", service)

    @property
    def catalogi_service(self):
        if self.default_zgw_api_group is None:
            return None
        return self.default_zgw_api_group.ztc_service

    @catalogi_service.setter
    def catalogi_service(self, service):
        return self._set_zgw_service("ztc_service", service)

    @property
    def document_service(self):
        if self.default_zgw_api_group is None:
            return None
        return self.default_zgw_api_group.drc_service

    @document_service.setter
    def document_service(self, service):
        return self._set_zgw_service("drc_service", service)

    @property
    def form_service(self):
        if self.default_zgw_api_group is None:
            return None

        return self.default_zgw_api_group.form_service

    @form_service.setter
    def form_service(self, service):
        return self._set_zgw_service("form_service", service)

    zaak_max_confidentiality = models.CharField(
        max_length=32,
        choices=VertrouwelijkheidsAanduidingen.choices,
        default=VertrouwelijkheidsAanduidingen.openbaar,
        verbose_name=_("Case confidentiality"),
        help_text=_("Select maximum confidentiality level of cases"),
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

    fetch_eherkenning_zaken_with_rsin = models.BooleanField(
        verbose_name=_(
            "Fetch Zaken for users authenticated with eHerkenning using RSIN"
        ),
        help_text=_(
            "If enabled, Zaken for eHerkenning users are fetched using the company RSIN (Open Zaak). "
            "If not enabled, Zaken are fetched using the KvK number (eSuite)."
        ),
        default=False,
    )

    title_text = models.TextField(
        verbose_name=_("Title text"),
        help_text=_(
            "The title/introductory text shown on the list view of 'Mijn aanvragen'."
        ),
        default=_(
            "Hier vindt u een overzicht van al uw lopende en afgeronde aanvragen."
        ),
    )

    # feature flags
    enable_categories_filtering_with_zaken = models.BooleanField(
        verbose_name=_("Enable category filtering based on zaken"),
        default=False,
        help_text=_(
            "If checked, the highlighted categories list on the homepage will consist "
            "of categories that are linked to ZaakTypen for which the DigiD authenticated "
            "user has at least one Zaak."
        ),
    )

    action_required_deadline_days = models.IntegerField(
        verbose_name=_("Standaard actie deadline termijn in dagen"),
        default=15,
        help_text=_("Aantal dagen voor gebruiker om actie te ondernemen."),
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
    service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Catalogus API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        related_name="catalogus_configs",
        null=False,
    )

    class Meta:
        ordering = ("domein", "rsin")

    def __str__(self):
        return f"{self.domein} - {self.rsin}"


class ZaakTypeConfig(models.Model):
    urls = ArrayField(
        models.URLField(
            verbose_name=_("Zaaktype URL"),
        ),
        default=list,
    )
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
    notify_status_changes = models.BooleanField(
        verbose_name=_("Notify of status changes"),
        default=False,
        help_text=_(
            "Whether the user should be notified of status changes for cases with this zaak type"
        ),
    )

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
    contact_subject_code = models.CharField(
        verbose_name=_("e-Suite 'onderwerp' code"),
        max_length=255,
        blank=True,
    )

    relevante_zaakperiode = models.PositiveIntegerField(
        verbose_name=_("Relevante zaakperiode"),
        blank=True,
        null=True,
        help_text=_(
            "Aantal maanden dat teruggekeken moet worden naar Zaken van deze zaaktypes."
        ),
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
        return " - ".join(b for b in bits if b)


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


class ZaakTypeStatusTypeConfig(models.Model):
    zaaktype_config = models.ForeignKey(
        "openzaak.ZaakTypeConfig",
        on_delete=models.CASCADE,
    )
    statustype_url = models.URLField(
        verbose_name=_("Statustype URL"),
        max_length=1000,
    )
    omschrijving = models.CharField(
        verbose_name=_("Omschrijving"),
        max_length=80,
    )
    statustekst = models.CharField(
        verbose_name=_("Statustekst"),
        max_length=1000,
    )
    zaaktype_uuids = ArrayField(
        models.UUIDField(
            verbose_name=_("Zaaktype UUID"),
        ),
        default=list,
    )

    # configuration
    status_indicator = models.CharField(
        blank=True,
        max_length=32,
        choices=StatusIndicators.choices,
        verbose_name=_("Statustype indicator"),
        help_text=_(
            "Determines what color will be shown to the user if a case is set to this status"
        ),
    )
    status_indicator_text = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Statustype indicator text"),
        help_text=_(
            "Determines the text that will be shown to the user if a case is set to this status"
        ),
    )
    document_upload_description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Document upload description"),
        help_text=_(
            "Description that will be shown above the document upload widget in a case detail page"
        ),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Frontend description"),
        help_text=_(
            "The text displayed in the case detail page for the status with this statustype"
        ),
    )
    notify_status_change = models.BooleanField(
        verbose_name=_("Notify of status change"),
        default=True,
        help_text=_(
            "Whether the user should be notfied if a case is set to this type of status"
        ),
    )
    action_required = models.BooleanField(
        verbose_name=_("Action required"),
        default=False,
        help_text=_(
            "Whether the status change notification should indicate that an action is required"
        ),
    )
    document_upload_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Document uploads"),
        help_text=_(
            "Enable document uploads for this statustype (override setting for case type)"
        ),
    )
    call_to_action_url = models.URLField(
        blank=True,
        default="",
        verbose_name=_("Call to action url"),
        help_text=_(
            "The url the user will be sent to by clicking on the call-to-action button"
        ),
    )
    call_to_action_text = models.CharField(
        max_length=48,
        blank=True,
        default="",
        verbose_name=_("Call to action text"),
        help_text=_("The text displayed on the call-to-action button"),
    )
    case_link_text = models.CharField(
        max_length=40,
        blank=True,
        default="",
        verbose_name=_("Case link text"),
        help_text=_(
            "The text that will be shown in the button that links to a case's detail page"
        ),
    )

    objects = ZaakTypeStatusTypeConfigQuerySet.as_manager()

    class Meta:
        verbose_name = _("Zaaktype Statustype Configuration")

        constraints = [
            UniqueConstraint(
                name="unique_zaaktype_config_statustype_url",
                fields=["zaaktype_config", "statustype_url"],
            )
        ]

    def __str__(self):
        return f"{self.zaaktype_config.identificatie} - {self.omschrijving}"


class ZaakTypeResultaatTypeConfig(models.Model):
    zaaktype_config = models.ForeignKey(
        "openzaak.ZaakTypeConfig",
        on_delete=models.CASCADE,
    )
    resultaattype_url = models.URLField(
        verbose_name=_("Resultaattype URL"),
        max_length=1000,
    )
    omschrijving = models.CharField(
        verbose_name=_("Omschrijving"),
        max_length=200,
    )
    zaaktype_uuids = ArrayField(
        models.UUIDField(
            verbose_name=_("Zaaktype UUID"),
        ),
        default=list,
    )

    # configuration
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Result description"),
        help_text=_(
            "Determines the text that will be shown to the user if a case is set to this result"
        ),
    )

    class Meta:
        verbose_name = _("Zaaktype Resultaattype Configuration")

        constraints = [
            UniqueConstraint(
                name="unique_zaaktype_config_resultaattype_url",
                fields=["zaaktype_config", "resultaattype_url"],
            )
        ]

    def __str__(self):
        return f"{self.zaaktype_config.identificatie} - {self.omschrijving}"


class UserCaseStatusNotificationBase(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
    )
    case_uuid = models.UUIDField(
        verbose_name=_("Zaak UUID"),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"), default=timezone.now
    )
    is_sent = models.BooleanField(_("Is sent"), default=False)
    collision_key = models.CharField(_("Collision key"), blank=True, max_length=255)

    def mark_sent(self):
        self.is_sent = True
        self.save(update_fields=["is_sent"])

    class Meta:
        abstract = True


class UserCaseStatusNotification(UserCaseStatusNotificationBase):
    status_uuid = models.UUIDField(
        verbose_name=_("Status UUID"),
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

    def has_received_similar_notes_within(
        self, period: timedelta, collision_key: str
    ) -> bool:
        return UserCaseStatusNotification.objects.has_received_similar_notes_within(
            self.user, self.case_uuid, period, collision_key, not_record_id=self.id
        )


class UserCaseInfoObjectNotification(UserCaseStatusNotificationBase):
    zaak_info_object_uuid = models.UUIDField(
        verbose_name=_("InformatieObject UUID"),
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

    def has_received_similar_notes_within(
        self, period: timedelta, collision_key: str
    ) -> bool:
        return UserCaseInfoObjectNotification.objects.has_received_similar_notes_within(
            self.user, self.case_uuid, period, collision_key, not_record_id=self.id
        )
