"""Fail-closed, permission-aware selectors for beneficiary data."""

from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.rbac.authorization import user_has_permission

from .constants import ConfidentialityLevel
from .models import Beneficiary
from .permissions import (
    BENEFICIARIES_MANAGE,
    BENEFICIARIES_MANAGE_DOCUMENTS,
    BENEFICIARIES_VIEW,
    BENEFICIARIES_VIEW_CONFIDENTIAL,
)


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def visible_beneficiaries(user, *, include_archived: bool = False) -> QuerySet:
    """Return only beneficiary records the actor may know exist."""
    queryset = Beneficiary.all_objects.filter(is_deleted=False).select_related(
        "category",
        "classification",
        "gender",
        "organization_unit",
        "primary_responsible_officer",
        "case_manager",
        "household",
        "verified_by",
    )
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    if not _authenticated(user):
        return queryset.none()
    if user.is_superuser or user_has_permission(user, BENEFICIARIES_MANAGE):
        return queryset.distinct()

    access_filter = Q()
    has_access_rule = False
    if user_has_permission(user, BENEFICIARIES_VIEW):
        access_filter |= (
            Q(created_by=user)
            | Q(primary_responsible_officer=user)
            | Q(case_manager=user)
        )
        has_access_rule = True
    if user_has_permission(user, BENEFICIARIES_VIEW_CONFIDENTIAL):
        access_filter |= Q(
            confidentiality__in=[
                ConfidentialityLevel.DIRECTORY,
                ConfidentialityLevel.INTERNAL,
                ConfidentialityLevel.CONFIDENTIAL,
            ]
        )
        has_access_rule = True
    if not has_access_rule:
        return queryset.none()
    return queryset.filter(access_filter).distinct()


def visible_beneficiary_documents(user, beneficiary=None) -> QuerySet:
    """Documents fail closed independently of profile visibility."""
    from .models import BeneficiaryDocument

    queryset = BeneficiaryDocument.objects.select_related(
        "beneficiary", "document_type", "uploaded_by"
    )
    if beneficiary is not None:
        queryset = queryset.filter(beneficiary=beneficiary)
    if not _authenticated(user):
        return queryset.none()
    if not (
        user.is_superuser
        or user_has_permission(user, BENEFICIARIES_MANAGE)
        or user_has_permission(user, BENEFICIARIES_MANAGE_DOCUMENTS)
    ):
        return queryset.none()
    return queryset.filter(
        beneficiary__in=visible_beneficiaries(user, include_archived=True)
    )


def user_can_access_beneficiary(user, beneficiary, *, include_archived=False) -> bool:
    """Object authorization helper used by transactional services."""
    if beneficiary is None:
        return False
    return (
        visible_beneficiaries(user, include_archived=include_archived)
        .filter(pk=beneficiary.pk)
        .exists()
    )
