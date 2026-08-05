"""Domain-specific exceptions for the program management module."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ProgramTransitionError(ValidationError):
    """Raised when a program status transition is not permitted."""

    def __init__(self, from_status: str, to_status: str):
        super().__init__(
            _("Transition from %(from)s to %(to)s is not allowed.")
            % {"from": from_status, "to": to_status},
            code="invalid_program_transition",
        )


class ProjectTransitionError(ValidationError):
    """Raised when a project status transition is not permitted."""

    def __init__(self, from_status: str, to_status: str):
        super().__init__(
            _("Transition from %(from)s to %(to)s is not allowed.")
            % {"from": from_status, "to": to_status},
            code="invalid_project_transition",
        )


class ProgramSelfApprovalError(ValidationError):
    """Raised when a program creator attempts to approve their own program."""

    def __init__(self):
        super().__init__(
            _("Program creators cannot approve their own programs."),
            code="program_self_approval",
        )


class ProgramArchiveProtectionError(ValidationError):
    """Raised when an attempt is made to archive an already archived program."""

    def __init__(self):
        super().__init__(
            _("Program is already archived."), code="program_already_archived"
        )
