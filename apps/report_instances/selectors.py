"""Selectors for report instances.

Permission-aware query functions that encapsulate common read patterns.
"""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.reports.constants import ReportStatus

from .models import Report, ReportVersion

# ---------------------------------------------------------------------------
# Single-object selectors
# ---------------------------------------------------------------------------


def get_report_by_id(report_id: str | Any) -> Report:
    """Return a report by PK or raise DoesNotExist."""
    return Report.objects.get(pk=report_id)


def get_report_or_404(report_id: str | Any) -> Report:
    """Return a report by PK or return 404."""
    return get_object_or_404(Report, pk=report_id)


def get_report_version_or_404(
    report_id: str | Any, version_number: int
) -> ReportVersion:
    """Return a specific version snapshot or raise 404."""
    return get_object_or_404(
        ReportVersion, report_id=report_id, version_number=version_number
    )


# ---------------------------------------------------------------------------
# Queryset selectors
# ---------------------------------------------------------------------------


def get_all_reports() -> QuerySet[Report]:
    """Return all non-deleted reports."""
    return Report.objects.filter(is_deleted=False)


def get_reports_by_owner(user: Any) -> QuerySet[Report]:
    """Return reports owned by the given user."""
    return get_all_reports().filter(owner=user)


def get_reports_by_reviewer(user: Any) -> QuerySet[Report]:
    """Return reports assigned to the given reviewer."""
    return get_all_reports().filter(assigned_reviewer=user)


def get_reports_by_status(status: str) -> QuerySet[Report]:
    """Return reports in a given status."""
    return get_all_reports().filter(status=status)


def get_draft_reports(user: Any | None = None) -> QuerySet[Report]:
    """Return draft reports, optionally filtered by owner."""
    qs = get_all_reports().filter(
        status__in={ReportStatus.DRAFT, ReportStatus.IN_PROGRESS}
    )
    if user is not None:
        qs = qs.filter(owner=user)
    return qs


def get_submitted_reports(user: Any | None = None) -> QuerySet[Report]:
    """Return submitted reports."""
    qs = get_all_reports().filter(
        status__in={
            ReportStatus.SUBMITTED,
            ReportStatus.UNDER_REVIEW,
            ReportStatus.RESUBMITTED,
        }
    )
    if user is not None:
        qs = qs.filter(owner=user)
    return qs


def get_reports_pending_review(user: Any) -> QuerySet[Report]:
    """Return reports pending review for a specific reviewer."""
    return get_all_reports().filter(
        assigned_reviewer=user,
        status__in={
            ReportStatus.SUBMITTED,
            ReportStatus.UNDER_REVIEW,
            ReportStatus.RESUBMITTED,
        },
    )


def get_approved_reports(user: Any | None = None) -> QuerySet[Report]:
    """Return approved reports."""
    qs = get_all_reports().filter(
        status__in={ReportStatus.APPROVED, ReportStatus.FINALIZED}
    )
    if user is not None:
        qs = qs.filter(owner=user)
    return qs


def get_archived_reports(user: Any | None = None) -> QuerySet[Report]:
    """Return archived reports."""
    qs = get_all_reports().filter(status=ReportStatus.ARCHIVED)
    if user is not None:
        qs = qs.filter(owner=user)
    return qs


def get_overdue_reports() -> QuerySet[Report]:
    """Return reports that are past their due date and not yet approved."""
    from django.utils import timezone

    return get_all_reports().filter(
        due_date__lt=timezone.now().date(),
        status__in={
            ReportStatus.DRAFT,
            ReportStatus.IN_PROGRESS,
            ReportStatus.SUBMITTED,
            ReportStatus.UNDER_REVIEW,
            ReportStatus.RETURNED_FOR_CORRECTION,
        },
    )


def get_reports_by_category(category_id: str | Any) -> QuerySet[Report]:
    """Return reports for a specific category."""
    return get_all_reports().filter(category_id=category_id)


def get_reports_by_template(template_id: str | Any) -> QuerySet[Report]:
    """Return reports created from a specific template."""
    return get_all_reports().filter(template_id=template_id)
