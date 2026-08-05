from .models import (
    ArchivableModel,
    BaseModel,
    CreatedByModel,
    IsActiveModel,
    NotesModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)


# Model Mixins - Aliased for convenience and consistent naming conventions
class UUIDMixin(UUIDModel):
    class Meta:
        abstract = True


class TimeStampedMixin(TimeStampedModel):
    class Meta:
        abstract = True


class CreatedByMixin(CreatedByModel):
    class Meta:
        abstract = True


class UpdatedByMixin(UpdatedByModel):
    class Meta:
        abstract = True


class SoftDeleteMixin(SoftDeleteModel):
    class Meta:
        abstract = True


class IsActiveMixin(IsActiveModel):
    class Meta:
        abstract = True


class NotesMixin(NotesModel):
    class Meta:
        abstract = True


class ArchiveMixin(ArchivableModel):
    class Meta:
        abstract = True


class BaseMixin(BaseModel):
    """
    BaseMixin provides a composite of common mixins:
    UUID, TimeStamped, CreatedBy, UpdatedBy, SoftDelete, and IsActive.
    """

    class Meta:
        abstract = True


class OwnershipMixin:
    """
    Mixin for verifying ownership of an object.
    Classes using this must define an owner or user field.
    """

    def is_owned_by(self, user):
        if hasattr(self, "created_by"):
            return self.created_by == user
        if hasattr(self, "user"):
            return self.user == user
        return False


class PermissionMixin:
    """
    Mixin for adding custom permission check logic at the model or view level.
    """

    def has_object_permission(self, user, permission_type):
        """
        Override this method in the child class to implement
        object-level permission checks.
        """
        return False


class ExportMixin:
    """
    Mixin for defining how an object should be exported.
    """

    def get_export_data(self):
        """
        Returns a dictionary representing the object for export.
        """
        raise NotImplementedError(
            "ExportMixin requires get_export_data to be implemented"
        )  # E501
