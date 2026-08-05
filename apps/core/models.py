import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .constants import StatusConstants
from .managers import BaseManager, SoftDeleteManager


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created_at`` and ``updated_at`` fields.
    """

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True


class CreatedByModel(models.Model):
    """
    An abstract base class model that provides a ``created_by`` field.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        verbose_name=_("Created by"),
    )

    class Meta:
        abstract = True


class UpdatedByModel(models.Model):
    """
    An abstract base class model that provides an ``updated_by`` field.
    """

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        verbose_name=_("Updated by"),
    )

    class Meta:
        abstract = True


class StatusModel(models.Model):
    """
    An abstract base class model that provides a ``status`` field.
    """

    status = models.CharField(
        _("Status"),
        max_length=50,
        choices=StatusConstants.choices,
        default=StatusConstants.DRAFT,
        db_index=True,
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    An abstract base class model that provides soft deletion functionality.
    """

    is_deleted = models.BooleanField(_("Is deleted"), default=False, db_index=True)
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
        verbose_name=_("Deleted by"),
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # noqa: DJ012

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, deleted_by=None):
        """
        Soft delete the object.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if deleted_by:
            self.deleted_by = deleted_by
        self.save(using=using, update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def hard_delete(self, using=None, keep_parents=False):
        """
        Permanently delete the object.
        """
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restore a soft-deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])


class ArchivableModel(models.Model):
    """
    An abstract base class model that provides archivable functionality.
    """

    is_archived = models.BooleanField(_("Is archived"), default=False, db_index=True)
    archived_at = models.DateTimeField(_("Archived at"), null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_archived",
        verbose_name=_("Archived by"),
    )

    class Meta:
        abstract = True

    def archive(self, archived_by=None):
        self.is_archived = True
        self.archived_at = timezone.now()
        if archived_by:
            self.archived_by = archived_by
        self.save(update_fields=["is_archived", "archived_at", "archived_by"])

    def unarchive(self):
        self.is_archived = False
        self.archived_at = None
        self.archived_by = None
        self.save(update_fields=["is_archived", "archived_at", "archived_by"])


class UUIDModel(models.Model):
    """
    An abstract base class model that provides a UUID primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class IsActiveModel(models.Model):
    """
    An abstract base class model that provides an ``is_active`` boolean field.
    """

    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    class Meta:
        abstract = True


class NotesModel(models.Model):
    """
    An abstract base class model that provides a ``notes`` text field.
    """

    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        abstract = True


class BaseModel(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    IsActiveModel,
):
    """
    A comprehensive abstract base model combining commonly required fields
    for primary business entities.
    """

    objects = BaseManager()
    all_objects = models.Manager()  # noqa: DJ012 - objects must be the default manager

    class Meta:
        abstract = True
