"""Fail-closed, permission-aware selectors for program data."""

from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.rbac.authorization import user_has_permission

from .models import Program, Project
from .permissions import (
    PROGRAMMES_MANAGE,
    PROGRAMMES_VIEW,
    PROJECTS_MANAGE,
    PROJECTS_VIEW,
)


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def visible_programs(user, *, include_archived: bool = False) -> QuerySet:
    """Return programs the actor may know exist."""
    manager = Program.all_objects if include_archived else Program.objects
    queryset = manager.select_related(
        "category", "portfolio", "program_manager", "responsible_directorate"
    )
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    if not _authenticated(user):
        return queryset.none()
    if user.is_superuser or user_has_permission(user, PROGRAMMES_MANAGE):
        return queryset

    if user_has_permission(user, PROGRAMMES_VIEW):
        return queryset.filter(
            Q(created_by=user)
            | Q(program_manager=user)
            | Q(team_members__user=user)
            | Q(program_manager__isnull=False)
        ).distinct()
    return queryset.none()


def visible_projects(user, *, include_archived: bool = False) -> QuerySet:
    """Return projects the actor may know exist, scoped by program visibility."""
    manager = Project.all_objects if include_archived else Project.objects
    queryset = manager.select_related(
        "program", "category", "project_manager", "program__portfolio"
    )
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    if not _authenticated(user):
        return queryset.none()
    if (
        user.is_superuser
        or user_has_permission(user, PROGRAMMES_MANAGE)
        or user_has_permission(user, PROJECTS_MANAGE)
    ):
        return queryset

    if user_has_permission(user, PROJECTS_VIEW):
        visible = visible_programs(user, include_archived=include_archived)
        return queryset.filter(
            Q(created_by=user) | Q(project_manager=user) | Q(program__in=visible)
        ).distinct()
    return queryset.none()


def user_can_access_program(user, program, *, include_archived=False) -> bool:
    if program is None:
        return False
    return (
        visible_programs(user, include_archived=include_archived)
        .filter(pk=program.pk)
        .exists()
    )


def user_can_access_project(user, project, *, include_archived=False) -> bool:
    if project is None:
        return False
    return (
        visible_projects(user, include_archived=include_archived)
        .filter(pk=project.pk)
        .exists()
    )
