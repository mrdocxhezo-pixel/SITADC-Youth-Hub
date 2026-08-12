# Phase 24 — Calendar & Meetings: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-08

**Status:** Implemented — stabilization pending (test suite requires fixes)

## Summary

Phase 24 implements the Calendar & Meetings module in a new `apps/meetings`
app, per `roadmaps/24-Calendar-and-Meetings.md`. The module provides
organizational calendars and calendar sharing, events with recurrence and
conflict detection, and a full meeting lifecycle: scheduling and rescheduling,
participant management with invitations and RSVP, versioned agendas, quorum
evaluation, attendance with check-in/out and immutable corrections, versioned
minutes, formal decisions with votes, action items with follow-up/escalation,
matters arising, venues, meeting templates, confidential-access logging, and
reminder commands. The module is wired into the RBAC framework (fresh installs
and existing databases), central reference numbering, and platform navigation.

## Architecture

- New Django app `apps/meetings` with **26 concrete models** on a shared
  `MeetingRecord` base (`UUIDModel`, `TimeStampedModel`, `CreatedByModel`,
  `UpdatedByModel`, plus `SoftDeleteModel`/`ArchivableModel`/`IsActiveModel`/
  `NotesModel` mixes): `CalendarTypeConfig`, `MeetingVenue`, `MeetingTemplate`,
  `Calendar`, `CalendarShare`, `CalendarEvent`, `EventOccurrence`,
  `EventReminder`, `Meeting`, `MeetingParticipant`, `MeetingInvitation`,
  `MeetingAgenda`, `AgendaItem`, `MeetingAttendance`,
  `AttendanceCorrectionRecord` (immutable), `MeetingMinutes`,
  `MinuteSection`, `MeetingDecision`, `DecisionVote`, `MeetingActionItem`,
  `ActionFollowUpRecord` (immutable), `MattersArising`,
  `MeetingScheduleHistory` (immutable), `MeetingDocument`,
  `MeetingActivityRecord` (immutable), `ConfidentialAccessLog` (immutable).
- **Meeting lifecycle**: DRAFT → SCHEDULED → CONFIRMED → IN_PROGRESS → COMPLETED
  → CLOSED, plus postponed/cancelled/archived, exercised through
  `MeetingService` with a validated transition map.
- **Service layer** (`services.py`): 16 concrete services on a shared
  `_MeetingServiceMixin` — calendar, calendar event (with conflict detection
  and recurrence expansion), meeting, participant, agenda, attendance, quorum,
  minutes, decision, action item, matters arising, reminder, meeting document,
  template, venue, and confidential-access services. All writes are
  permission-gated, transaction-backed, audited into the immutable
  `MeetingActivityRecord` timeline, and allocate reference numbers via the
  central `ReferenceNumberService`.
- **Recurrence engine** (`recurrence.py`): bounded, deterministic expansion
  (DAILY/WEEKLY/MONTHLY/QUARTERLY/ANNUALLY with interval, weekdays,
  count/until, day/month-of-year; max 500 occurrences / 1095-day range).
- **Selectors** (`selectors.py`): fail-closed, confidentiality-aware read
  layer (`visible_calendars`, `visible_events`, `visible_meetings`,
  `upcoming_*`, `overdue_actions`, and form-choice querysets).
- **Permissions** (`permissions.py`): three categories — `calendars` (10),
  `events` (14), `meetings` (36) — plus helper functions
  (`user_can_view_calendars/events/meetings/confidential`, export, schedule,
  attendance/minutes/action management, organizer/owner/share checks).
- **Views/URLs**: 76 permission-checked view classes and an 81-route
  `meetings` namespace covering calendars, events, meetings, participants,
  attendance, agendas, minutes, decisions, action items, documents, templates,
  venues, and exports (CSV/JSON/XLSX/DOCX/PDF).
- **RBAC**: `calendars`, `events`, and `meetings` permission categories added
  to `apps/rbac/seed_data.py` and seeded for existing databases by
  `apps/rbac/migrations/0016_seed_meeting_permissions.py` (`atomic=False`).
- **Reference numbering**: 6 schemes seeded by
  `apps/references/migrations/0010_seed_meeting_reference_schemes.py`
  (`calendar`/CAL, `event`/EVT, `meeting`/MTG, `meeting_minutes`/MIN,
  `meeting_decision`/DEC, `meeting_action`/ACT).

## Files Created

- `apps/meetings/` — full module: `models.py`, `services.py`, `selectors.py`,
  `views.py`, `forms.py`, `permissions.py`, `urls.py`, `admin.py`, `apps.py`,
  `constants.py`, `recurrence.py`, `validators.py`, `exceptions.py`,
  `exports.py`, `migrations/0001_initial.py`.
- `apps/meetings/templates/meetings/` — 30 Bootstrap 5 templates (dashboard,
  directories, details, forms, workflow/action pages, includes).
- `apps/meetings/tests/` — shared scaffold (`base.py`) plus 7 test modules:
  `test_models.py`, `test_forms.py`, `test_services.py`, `test_views.py`,
  `test_permissions.py`, `test_selectors.py`, `test_commands.py`.
- `apps/meetings/management/commands/` — `send_meeting_reminders`,
  `archive_old_meetings`, `cleanup_meeting_data`, `validate_meeting_data`,
  `generate_meeting_references`.
- `apps/rbac/migrations/0016_seed_meeting_permissions.py` — RBAC seed
  migration for existing databases.
- `apps/references/migrations/0010_seed_meeting_reference_schemes.py` —
  meeting/calendar/event reference scheme seeding.
- `docs/development/PHASE24_MEETINGS_REPORT.md` (this file).

## Files Modified

- `apps/rbac/seed_data.py` — `calendars`, `events`, `meetings` permission
  categories and role grants.
- `config/settings/base.py` — `apps.meetings.apps.MeetingsConfig` added to
  `INSTALLED_APPS`.
- `config/urls.py` — `meetings/` path with `meetings` namespace.
- `templates/components/sidebar.html` — Calendar & Meetings navigation item
  gated on `meetings.view` / `calendars.view` / `meetings.manage`.
- `apps/references/constants.py` — `ReferenceModules.CALENDARS/EVENTS/MEETINGS`.
- `CHANGELOG.md` and `DEVELOPMENT_STATUS.md` — Phase 24 entries.

## Database Changes

- `meetings.0001` — initial schema for all 26 tables with indexes and
  constraints (depends on `documents.0001`, `organizations.0002`, `programs.0006`,
  `rbac.0016_seed_meeting_permissions`).
- `rbac.0016` — new seed migration (3 categories, 60 permissions, role grants),
  reversible.
- `references.0010` — 6 reference scheme seeds, reversible.
  `makemigrations --check --dry-run` is clean.

## Security Considerations

- Server-side authorization only: every view goes through
  `MeetingPermissionMixin` with `meetings.manage` override; the UI never relies
  on hidden buttons.
- Secret/confidential rows are excluded from selectors unless the user holds a
  view-confidential permission; `ConfidentialAccessLog` records each access.
- Immutable records (`MeetingActivityRecord`, `AttendanceCorrectionRecord`,
  `ActionFollowUpRecord`, `MeetingScheduleHistory`) reject mutation; admin
  exposes them read-only.
- Meeting/event conflict detection and transition validation (including
  reschedule/postpone/cancel) are enforced in the service layer.
- Exports are permission-gated, audited, and formula-safe for CSV.
- Tests assert deny-by-default, fail-closed 403/302, and per-action
  permission enforcement.

## Tests Added

- 152 tests across 7 modules in `apps/meetings/tests/`: models (defaults,
  constraints, immutability), forms, services (calendar/event/meeting
  lifecycle, recurrence, attendance, minutes, decisions, actions, quorum),
  views (auth, permission fail-closed, workflow actions), permissions,
  selectors (visibility scoping), and management commands.
- **Stabilization status (2026-08-10 verification run):** 55 of 152 passed;
  **97 failing** across views, permissions, services, selectors, forms, and
  commands. Representative failure causes:
  - `MeetingAgenda` has no `all_objects` manager (used by the
    `cleanup_meeting_data` command's soft-delete cleanup).
  - Form/selector tests construct rows that violate the unique
    `reference`/`(calendar, …)` constraints or pass required fields that the
    current forms reject (validation/required-field drift between model and
    forms).
  - `NoReverseMatch` for `meetings:event_create` and other named routes;
    some permission/URL tests expect different redirect semantics (302 vs
    200/404) and reverse names.
  - `MeetingService.transition` raises `InvalidTransitionError` from DRAFT to
    `confirm` (status-action mapping drift between services/validators and
    views/tests).
  - Missing model reverse managers (`Meeting.actions`, `Meeting.minutes`)
    relied on by permission tests.
  - Reference-generation command tests require a superuser.
  These are stabilization tasks for completion before Phase 24 acceptance.

## Quality Gates

- Ruff/Black/isort: clean on `apps/meetings` and touched shared files.
- No new lint findings introduced.

## Documentation Updated

- `DEVELOPMENT_STATUS.md` — Phase 24 status section and module status row.
- `CHANGELOG.md` — Phase 24 entry.

## Known Notes

- `apps/meetings` consolidates the calendar domain (no separate
  `calendar_events` app is needed).
- Reminder delivery currently logs rather than integrates a mail transport;
  notification-engine integration is deferred to the notifications phase.
- **Phase 24 is not yet acceptance-ready**: the 152-test suite has 97 failing
  cases (see Tests Added). Application code and tests must be reconciled
  before the phase can be marked complete.

## Next Recommended Task

Stabilize Phase 24 (`apps/meetings` test suite: all_objects manager,
status/action transition mapping, route/redirect corrections, form/model and
constraint alignment, reverse-manager wiring, reference-command superuser
setup), then proceed to Phase 25 — Notifications & Announcements
(`roadmaps/25-Notifications-and-Announcements.md`).