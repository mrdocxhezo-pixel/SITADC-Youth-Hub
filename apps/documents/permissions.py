"""Permission helpers for the Document Management module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from apps.rbac.authorization import user_has_permission

from .constants import ConfidentialityLevel, DocumentPermissions

if TYPE_CHECKING:
    from .models import Document

    User = get_user_model()


def _check(user: User, perm: str) -> bool:
    return user_has_permission(user, perm)


# ---------------------------------------------------------------------------
# Global Permissions
# ---------------------------------------------------------------------------


def can_view_documents(user: User) -> bool:
    return _check(user, DocumentPermissions.VIEW)


def can_upload_documents(user: User) -> bool:
    return _check(user, DocumentPermissions.UPLOAD)


def can_create_documents(user: User) -> bool:
    return _check(user, DocumentPermissions.CREATE)


def can_manage_categories(user: User) -> bool:
    return _check(user, DocumentPermissions.MANAGE_CATEGORIES)


def can_manage_types(user: User) -> bool:
    return _check(user, DocumentPermissions.MANAGE_TYPES)


def can_manage_folders(user: User) -> bool:
    return _check(user, DocumentPermissions.MANAGE_FOLDERS)


def can_manage_tags(user: User) -> bool:
    return _check(user, DocumentPermissions.MANAGE_TAGS)


def can_manage_retention(user: User) -> bool:
    return _check(user, DocumentPermissions.MANAGE_RETENTION)


def can_view_audit(user: User) -> bool:
    return _check(user, DocumentPermissions.VIEW_AUDIT)


def can_approve_disposal(user: User) -> bool:
    return _check(user, DocumentPermissions.APPROVE_DISPOSAL)


# ---------------------------------------------------------------------------
# Object-Level Permissions
# ---------------------------------------------------------------------------


def can_view_document(user: User, document: Document) -> bool:
    if not _check(user, DocumentPermissions.VIEW):
        return False
    if document.owner_id == user.id:
        return _check(user, DocumentPermissions.VIEW_OWN)
    if document.is_sensitive and not _check(user, DocumentPermissions.VIEW_SENSITIVE):
        return False
    return not (
        document.confidentiality_level
        in (
            ConfidentialityLevel.CONFIDENTIAL,
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
            ConfidentialityLevel.BOARD,
            ConfidentialityLevel.EXECUTIVE,
        )
        and not _check(user, DocumentPermissions.VIEW_CONFIDENTIAL)
    )


def can_update_metadata(user: User, document: Document) -> bool:
    if not _check(user, DocumentPermissions.UPDATE_METADATA):
        return False
    if document.owner_id == user.id:
        return True
    return _check(user, DocumentPermissions.UPDATE_METADATA)


def can_upload_version(user: User, document: Document) -> bool:
    if not _check(user, DocumentPermissions.UPLOAD_VERSION):
        return False
    return document.owner_id == user.id or _check(
        user, DocumentPermissions.UPLOAD_VERSION
    )


def can_checkout(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.CHECKOUT)


def can_checkin(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.CHECKIN)


def can_cancel_checkout(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.CANCEL_CHECKOUT)


def can_submit(user: User, document: Document) -> bool:
    if not _check(user, DocumentPermissions.SUBMIT):
        return False
    return document.owner_id == user.id or document.created_by_id == user.id


def can_review(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.REVIEW)


def can_return_for_correction(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.RETURN_FOR_CORRECTION)


def can_approve(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.APPROVE)


def can_publish(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.PUBLISH)


def can_unpublish(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.UNPUBLISH)


def can_archive(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.ARCHIVE)


def can_restore(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.RESTORE)


def can_request_disposal(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.REQUEST_DISPOSAL)


def can_download(user: User, document: Document) -> bool:
    if document.download_restricted:
        return False
    return _check(user, DocumentPermissions.DOWNLOAD)


def can_print(user: User, document: Document) -> bool:
    if document.print_restricted:
        return False
    return _check(user, DocumentPermissions.PRINT)


def can_share_internal(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.SHARE_INTERNAL)


def can_share_external(user: User, document: Document) -> bool:
    return _check(user, DocumentPermissions.SHARE_EXTERNAL)


def can_view_history(user: User) -> bool:
    return _check(user, DocumentPermissions.VIEW_HISTORY)
