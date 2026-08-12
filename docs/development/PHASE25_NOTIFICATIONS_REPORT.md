# Phase 25 — Notifications & Announcements: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-09

**Status:** Implemented (pending acceptance)

## Summary

Phase 25 implements the Notifications & Announcements module in a new
`apps/notifications` app, per `roadmaps/25-Notifications-and-Announcements.md`.
The module provides per-recipient notifications with categories, priorities,
channels, preferences, quiet hours and digests; event-driven rules and message
templates; delivery tracking with retry/backoff and expiry; immutable audit and
event records; and managed system announcements with audience targeting,
publishing, dismissal and acknowledgement. The module is wired into the RBAC
framework (fresh installs and existing databases), central reference numbering,
the notification bell in the top navigation, and a background processing
command.

## Architecture

- New Django app `apps/notifications` with **12 concrete models** on a shared
  `NotificationRecord` base (`UUIDModel`, `TimeStampedModel`, `CreatedByModel`,
  `UpdatedByModel`): `NotificationEvent` (immutable domain event),
  `NotificationCategory`, `Notification`, `NotificationTemplate`,
  `NotificationRule`, `NotificationPreference`, `NotificationDelivery`,
  `SystemAnnouncement`, `AnnouncementDelivery`, `AnnouncementDismissal`,
  `NotificationAuditRecord` (immutable), `NotificationDigest` (plus a
  deprecated `Announcement` proxy alias).
- **Service layer** (`services.py`): 15 concrete services on
  `apps.core.services.BaseService` — notification creation/rendering/dedup,
  send, mark-read/mark-all-read, acknowledge, archive, event processing,
  announcement create/publish/unpublish, preference management, template and
  rule management, delivery processing, expiry processing, and digest
  generation. All writes are permission-gated, transaction-backed, audited
  into the immutable `NotificationAuditRecord` timeline, and allocate
  reference numbers via the central `ReferenceNumberService`.
- **Preference engine**: per-user channel toggles, digest frequency, quiet
  hours, and category preferences with `category_allowed()`,
  `channel_enabled()`, `in_quiet_hours()`.
- **Managers** (`managers.py`): 7 manager/queryset pairs providing
  `for_user`, `unread`, `action_required`, `active`, `pending_delivery`,
  `unread_count_for`, template/rule/preference/delivery/announcement query
  helpers.
- **Selectors** (`selectors.py`): fail-closed read layer (notification
  inbox scopes, digests, announcements with dismissal awareness, unread/action
  counts, category/announcement summaries).
- **Permissions** (`permissions.py`): three categories — `notifications` (9),
  `announcements` (6), `preferences` (3) — plus helper functions
  (`user_can_view/manage_notifications`, template/rule/configure/send,
  publish/manage announcements, update preferences, recipient/author checks).
- **Views/URLs**: 25 permission-checked view classes and a 25-route
  `notifications` namespace (dashboard, inbox, notification detail and actions,
  preferences, template/rule directories and forms, announcement directory/
  forms/publish/unpublish/dismiss, event directory, audit log, and JSON APIs
  for unread count and recent notifications).
- **RBAC**: `notifications`, `announcements`, and `preferences` permission
  categories added to `apps/rbac/seed_data.py` and seeded for existing
  databases by `apps/rbac/migrations/0017_seed_notification_permissions.py`
  (`atomic=False`).
- **Reference numbering**: 2 schemes seeded by
  `apps/references/migrations/0011_seed_notification_reference_schemes.py`
  (`notification`/NTF and `announcement`/ANN).
- **Front-end integration**: `static/js/notifications.js` drives the
  notification bell badge (60s polling via the JSON APIs), dropdown rendering,
  and AJAX mark-read/dismiss with CSRF.

## Files Created

- `apps/notifications/` — full module: `models.py`, `services.py`,
  `selectors.py`, `views.py`, `forms.py`, `permissions.py`, `urls.py`,
  `admin.py`, `apps.py`, `managers.py`, `constants.py`, `validators.py`,
  `exceptions.py`, `migrations/0001_initial.py`.
- `apps/notifications/templates/notifications/` — 14 Bootstrap 5 templates
  (dashboard, inbox, detail, preference/template/rule/announcement forms and
  directories, event directory, audit directory, includes).
- `apps/notifications/tests/` — shared scaffold (`base.py`) plus 5 test
  modules: `test_models.py`, `test_services.py`, `test_views.py`,
  `test_permissions.py`, `test_selectors.py`.
- `apps/notifications/management/commands/process_notifications.py` —
  delivery/dispatch and expiry background processing command.
- `static/js/notifications.js` — notification bell badge/dropdown/AJAX logic.
- `apps/rbac/migrations/0017_seed_notification_permissions.py` — RBAC seed
  migration for existing databases.
- `apps/references/migrations/0011_seed_notification_reference_schemes.py` —
  notification/announcement reference scheme seeding.
- `docs/development/PHASE25_NOTIFICATIONS_REPORT.md` (this file).

## Files Modified

- `apps/rbac/seed_data.py` — `notifications`, `announcements`, `preferences`
  permission categories and role grants.
- `config/settings/base.py` — `apps.notifications.apps.NotificationsConfig`
  added to `INSTALLED_APPS`.
- `config/urls.py` — `notifications/` path with `notifications` namespace.
- `templates/components/sidebar.html` — Notifications navigation item gated on
  `notifications.view` / `notifications.manage`.
- `templates/components/top_nav.html` — notification bell dropdown.
- `templates/layouts/dashboard.html` — loads `static/js/notifications.js`.
- `apps/references/constants.py` — `ReferenceModules.NOTIFICATIONS` and
  `ReferenceModules.ANNOUNCEMENTS`.
- `CHANGELOG.md` and `DEVELOPMENT_STATUS.md` — Phase 25 entries.

## Database Changes

- `notifications.0001` — initial schema for all 12 tables with indexes and
  constraints (unique event source, unique rule event-name, unique
  announcement dismissal/delivery; depends on `organizations.0002` and
  `rbac.0017_seed_notification_permissions`).
- `rbac.0017` — new seed migration (3 categories, 19 permissions, role
  grants), reversible.
- `references.0011` — 2 reference scheme seeds, reversible.
  `makemigrations --check --dry-run` is clean.

## Security Considerations

- Server-side authorization only: every view goes through
  `NotificationPermissionMixin` (extends `LoginRequiredMixin`); the UI never
  relies on hidden buttons.
- Recipient scoping: functions like `is_recipient` restrict reads to the
  notification's owner; announcements are audience-gated.
- Open-redirect protection on the deep-link notification redirect view.
- Template variables are allowlist-validated; delivery error summaries are
  sanitized.
- Immutable records (`NotificationAuditRecord`, `NotificationEvent`) reject
  mutation; admin exposes audit/event/delivery tables read-only.
- Tests assert deny-by-default, fail-closed 403/302, and per-action
  permission enforcement.

## Tests Added

- 121 tests across 5 modules in `apps/notifications/tests/`: models (defaults,
  auto-expiry, constraints, immutability), services (creation/rendering/dedup,
  send/read/acknowledge/archive, announcements publish/unpublish, preferences,
  templates/rules, delivery processing, digests), views (inbox, actions,
  announcements, preferences, JSON APIs, permission fail-closed), permissions,
  and selectors (scoping, counts, summaries).

## Quality Gates

- Ruff/Black/isort: clean on `apps/notifications` and touched shared files.
- No new lint findings introduced.

## Documentation Updated

- `DEVELOPMENT_STATUS.md` — Phase 25 status section and module status row.
- `CHANGELOG.md` — Phase 25 entry.

## Known Notes

- Delivery is provider-agnostic (in-app delivery is immediate; external
  channels are dispatched by `process_notifications` and record
  retry/backoff); mail integration is deferred to its owning phase.
- The `Announcement` proxy is retained only for backwards compatibility.

## Next Recommended Task

Proceed to Phase 26 — Global Search
(`roadmaps/26-Global-Search.md`).