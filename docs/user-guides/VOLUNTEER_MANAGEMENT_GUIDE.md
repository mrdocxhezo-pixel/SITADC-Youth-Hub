# Volunteer Management Guide

**Module:** `apps.volunteers`

**Phase:** 13 — Volunteer Management

**Status:** Stabilization; not yet accepted

## Access

Volunteer pages are under `/volunteers/`. Authentication and the centralized `volunteers.*` RBAC permissions are enforced server-side. Users with only `volunteers.view` can access their own profile. Officers with module permissions can access the registry and operational records. Contact, emergency, identity, document, and confidential export data require `volunteers.view_confidential`.

## Recruitment And Applications

1. An authorized officer creates a campaign from **Volunteers → Recruitment → New Campaign**.
2. The system assigns and confirms a `VRC-SITADC-YYYY-NNNNNN` campaign reference.
3. An applicant opens `/volunteers/apply/`, chooses an open campaign when applicable, confirms consent, and submits the form.
4. The system stores an uploaded CV privately and assigns a `VAP-SITADC-YYYY-NNNNNN` reference.
5. The applicant receives a one-time non-sensitive receipt page. Application details remain staff-protected.

## Screening And Interview

Authorized officers move an application from **Submitted** to **Under Screening**. Screening cannot pass until identity, references, qualifications, and safeguarding checks are complete. A passed screening becomes **Shortlisted**. An interview records its schedule, score from 0 to 100, recommendation, and pass result. Completed interviews move to **Interviewed**, after which an officer may approve or reject the application.

## Registration And Onboarding

An approved application can be registered against an active user account that has no volunteer profile. The central numbering service assigns a permanent `VOL-SITADC-YYYY-NNNNNN` reference. Required orientation, code of conduct, safeguarding, and confidentiality acknowledgements must be complete before onboarding can finish. Completed onboarding activates the volunteer and can mark the ID card as issued.

## Profiles And Privacy

The directory supports search, status/category filters, and pagination. Profile contact and emergency fields are hidden unless the actor has confidential access. Staff updates pass through the service layer and produce an audit record. Soft-deleted or archived records are excluded from ordinary queries.

## Assignments And Attendance

Only eligible registered or active volunteers can receive assignments. Assignment closure creates immutable deployment history. Attendance rejects future dates, duplicate activity/date records, service hours outside 0–24, and hours on absent/excused entries.

## Training, Performance, And Recognition

Training validates completion dates and stores certificates privately. Performance scores must be 1–100 and each volunteer can have one review per named period. Recognition records are created through an audited service.

## Leave And Exit

Leave dates must be ordered and cannot overlap submitted or approved leave. Only submitted leave can be approved or rejected. A current approved leave moves an eligible profile to **On Leave**. Exit completion requires asset and document clearance, closes active assignments, records deployment history, and transitions the profile to **Exited** or **Alumni**.

## Reports And Exports

The current report surface exports a permission-scoped CSV volunteer register. Spreadsheet formula prefixes are neutralized. Contact columns are included only with confidential permission. Every export is audited and returned with private, no-store caching headers.

## Records And Files

Audit and status records are append-only through supported application APIs. CVs, certificates, and volunteer documents are stored under `PRIVATE_MEDIA_ROOT`, outside public `MEDIA_URL`. Direct storage URLs are prohibited. Authorized CV downloads use a protected endpoint and create an audit record.

## Known Limitations

Phase 13 is not accepted because activity logging, disciplinary workflows, configurable database-backed taxonomies, versioned document retention/approval, and PDF/DOCX/XLSX reports remain outstanding. Program and project relationships remain compatibility text fields until those later modules expose stable models.
