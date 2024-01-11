from typing import Optional, Union
from uuid import UUID

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from open_inwoner.accounts.models import User
from open_inwoner.userfeed.choices import FeedItemType


class FeedItemManager(models.Manager):
    def mark_uuid_completed(
        self,
        user: User,
        type: FeedItemType,
        ref_uuid: Union[str, UUID],
        ref_key: Optional[str] = None,
        force: bool = False,
    ):
        qs = self.filter(
            user=user,
            type=type,
            ref_uuid=ref_uuid,
        )
        if ref_key is not None:
            qs = qs.filter(ref_key=ref_key)
        return qs.mark_completed(force=force)

    def mark_object_completed(
        self,
        user: User,
        type: FeedItemType,
        ref_object: models.Model,
        ref_key: Optional[str] = None,
        force: bool = False,
    ):
        qs = self.filter(
            user=user,
            type=type,
        ).filter_ref_object(ref_object)

        if ref_key is not None:
            qs = qs.filter(ref_key=ref_key)
        return qs.mark_completed(force=force)


class FeedItemQueryset(models.QuerySet):
    def mark_completed(self, force: bool = False):
        qs = self
        if not force:
            qs = qs.filter(
                completed_at__isnull=True,
            )
        # note: this must match with the instance method
        return qs.update(
            completed_at=timezone.now(),
        )

    def filter_ref_object(
        self, ref_object: models.Model
    ) -> models.QuerySet["FeedItemData"]:
        return self.filter(
            ref_object_id=ref_object.id,
            ref_object_type=ContentType.objects.get_for_model(ref_object),
        )


class FeedItemData(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
    )
    display_at = models.DateTimeField(
        verbose_name=_("Feed time"),
        default=timezone.now,
    )
    completed_at = models.DateTimeField(
        verbose_name=_("Information seen or action completed"),
        blank=True,
        null=True,
    )

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    auto_expire_at = models.DateTimeField(
        verbose_name=_("Automatically mark as completed after"),
        blank=True,
        null=True,
    )

    action_required = models.BooleanField(
        verbose_name=_("Action required"),
        default=False,
    )

    type = models.CharField(
        _("Type"),
        max_length=64,
        choices=FeedItemType.choices,
    )
    type_data = models.JSONField(
        verbose_name=_("Data for type"),
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
    )

    # for lookup and de-duplication
    ref_uuid = models.UUIDField(_("External object UUID"), null=True, blank=True)
    ref_key = models.CharField(
        _("External object de-duplication"), blank=True, max_length=64
    )
    ref_object_field = GenericForeignKey(
        ct_field="ref_object_type", fk_field="ref_object_id"
    )
    ref_object_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True
    )
    ref_object_id = models.PositiveIntegerField(blank=True, null=True)

    @cached_property
    def ref_object(self) -> Optional[models.Model]:
        # don't raise but return None
        if self.ref_object_type_id and self.ref_object_id:
            return self.ref_object_field

    objects = FeedItemManager.from_queryset(FeedItemQueryset)()

    def mark_completed(self, force: bool = False, save: bool = True):
        # note: this must match with the queryset method
        if self.completed_at is None or force:
            self.completed_at = timezone.now()
        if save:
            self.save()

    class Meta:
        ordering = ["display_at"]
        indexes = [
            models.Index(fields=["user", "type"], name="user_type"),
        ]
        constraints = [
            CheckConstraint(
                # don't allow setting both uuid and generic object for now
                check=Q(
                    # uuid
                    ref_uuid__isnull=False,
                    ref_object_type__isnull=True,
                    ref_object_id__isnull=True,
                )
                | Q(
                    # object
                    ref_uuid__isnull=True,
                    ref_object_type__isnull=False,
                    ref_object_id__isnull=False,
                )
                | Q(
                    # none
                    ref_uuid__isnull=True,
                    ref_object_type__isnull=True,
                    ref_object_id__isnull=True,
                ),
                name="enforce_single_main_ref_field",
            ),
        ]

    def __str__(self):
        return f"{self.type} {self.user} @ {self.display_at}"
