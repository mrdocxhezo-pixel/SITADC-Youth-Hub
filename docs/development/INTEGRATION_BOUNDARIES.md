# Integration Boundaries

**Scope:** Phase 14 Stakeholder Management
**Status:** Stable for current dependencies; later integrations deferred

## Existing Dependencies

The stakeholder domain may depend directly on these stable applications:

- `accounts`: authenticated users and actor attribution
- `rbac`: permission evaluation and scope checks
- `organizations`: organizational ownership and geographic scope
- `references`: atomic reference reservation and confirmation
- `leadership`: leadership ownership where an existing relationship is required

Operational writes must continue through stakeholder services. Views should
use validated forms and selectors; templates must not implement authorization
or business rules.

## Deferred Ports

The following boundaries are intentionally deferred until their owning modules
provide stable APIs:

| Future domain | Boundary contract |
| --- | --- |
| Programs and Projects | Optional foreign-key/rollup adapters for contributions, commitments, and reporting context |
| Documents | Protected document storage, versioning, retention, approval, and download audit adapter |
| Notifications | Event-to-notification adapter for expiry, assignment, approval, and follow-up alerts |
| Reports | Scoped report data providers and report-template references |
| MEAL | Indicator, outcome, monitoring, and evaluation references |
| Audit | Immutable central event sink for stakeholder domain events |
| Dashboard | Role-aware aggregate cards and drill-down providers |
| Search and Registers | Permission-aware indexing and register export providers |

Until a deferred owner exposes an API, stakeholder records must not import its
models, create duplicate tables, or invent foreign keys to an absent app.
Existing compatibility fields and service-level adapters must remain explicit
and replaceable.

## Acceptance Rule

An integration can be enabled only when the owning module provides:

1. A documented model/service contract.
2. Server-side permission and organizational-scope behavior.
3. Migration-safe identifiers and lifecycle semantics.
4. Tests covering authorized, unauthorized, missing, and archived records.
5. An audit and failure-handling strategy.

This boundary is the reason Phase 15 and later implementation must wait for
Phase 14 acceptance and the required dependency modules.
