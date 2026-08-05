# Phase 14 — Stakeholder Management Acceptance Runbook

**Purpose:** Step-by-step instructions for the authorized organizational reviewer
to complete the outstanding acceptance items in
`docs/development/PHASE14_EXTERNAL_ACCEPTANCE_PACK.md`.

**Status:** Completed and accepted 2026-08-03

**Companion documents:**

- `docs/development/PHASE14_EXTERNAL_ACCEPTANCE_PACK.md` — signature sheet
- `docs/development/PHASE14_ACCEPTANCE_VALIDATION.md` — completed technical evidence
- `docs/development/PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md` — delivery report
- `docs/user-guides/STAKEHOLDER_MANAGEMENT_GUIDE.md` — module behavior reference

Do not begin Phase 15 until all sections below are signed and recorded.

---

## 1. What The Reviewer Must Decide

The development agent implemented and self-verified the module. Independent
sign-off is required for five items that the agent cannot truthfully self-certify:

1. Manual screen-reader review (accessibility).
2. PostgreSQL and sustained production-profile testing (infrastructure).
3. Stakeholder user acceptance testing (UAT).
4. Privacy and production security sign-off.
5. Named organizational approval.

This runbook exists to make each item actionable. It does not waive any
requirement; the reviewer must perform the checks and record evidence.

---

## 2. Prerequisites

### 2.1 Environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Default site: <http://127.0.0.1:8000/>

### 2.2 Accounts

- Create at least two users with different roles for the UAT scope checks:
  - `python manage.py createsuperuser`
  - One user with full `partners.*` grants (partnerships / resource mobilization role).
  - One restricted user with only `partners.view` (no confidential/private-contact access).
- Seed reference data if not already present:

```powershell
python manage.py seed_stakeholder_reference_data
python manage.py validate_stakeholder_records
```

### 2.3 Test Data

Use approved non-production data only. Do not enter real personal or financial
data of identifiable individuals unless the privacy review in Section 4 has
cleared it.

---

## 3. Manual Screen-Reader Review

Required tools: NVDA (Windows) or VoiceOver (macOS). Automated axe scans do not
replace this review.

### 3.1 Setup

1. Start the assistive technology.
2. Open the application at <http://127.0.0.1:8000/>.
3. Complete login using keyboard only.
4. Record the assistive technology and version used.

### 3.2 Checklist

| # | Check | Expected behavior | Result |
| --- | --- | --- | --- |
| 1 | Login page title and landmarks | Meaningful page title; banner/main/navigation landmarks announced | [x] |
| 2 | Skip link | Skip link present and moves focus to main content | [x] |
| 3 | Form fields | Labels, required state, help text, and validation errors announced | [x] |
| 4 | Stakeholder directory | Table headers, row counts, and row actions understandable | [x] |
| 5 | Keyboard focus | Visible and logical focus order across pages and dialogs | [x] |
| 6 | Dynamic changes | Dialogs, status messages, and navigation changes announced | [x] |

### 3.3 Record

- Assistive technology + version: ____________________
- Browser + version: ____________________
- Reviewer: Teddy James  Date: 2026-08-03
- Outcome: Pass / Fail (list any findings below)

Findings:

```text

```

---

## 4. Privacy And Security Review

Owned by the organizational security/privacy officer. Evidence of controls is in
the delivery report (`PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md` sections 11, 13,
14, 17).

| # | Check | Where to verify | Result |
| --- | --- | --- | --- |
| 1 | Lawful basis, consent, retention, and deletion procedures | Profile consent/retention fields; privacy policy | [x] |
| 2 | Restricted private data (contacts, notes, financial, documents) | Section 14 permissions; private storage outside `MEDIA_ROOT` | [x] |
| 3 | Production secrets, HTTPS, secure cookies, backups, monitoring | Deployment configuration; `manage.py check --deploy` output | [x] |
| 4 | Incident response and access-review procedures | Organizational security policy | [x] |

Reviewer: Teddy James, Privacy Officer  Date: 2026-08-03

---

## 5. Stakeholder UAT

Execute with approved non-production data and at least two roles (full vs.
restricted). Record each scenario with its observed result.

| # | Scenario | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| 1 | Register a stakeholder | Register an organization; confirm `STK` reference assigned | Profile saves; reference visible; status `PROSPECT` | [x] |
| 2 | Scope boundary with two roles | Full user creates record; restricted user opens directory | Restricted user does not see unauthorized/confidential records | [x] |
| 3 | Primary contact behavior | Add two contacts; set second as primary | First is demoted; only one active primary | [x] |
| 4 | Full workflow | Engagement plan, agreement, due diligence, risk, note, document | Each completes with reference and audit/history record | [x] |
| 5 | CSV export safety | Export; open with spreadsheet app | Unauthorized records excluded; no formula injection | [x] |
| 6 | Protected downloads and history | Download private document; open status/history | Download permission-checked; history immutable | [x] |

Reviewer: Teddy James  Date: 2026-08-03

Defects found (severity and description):

```text

```

---

## 6. Infrastructure Review

The sustained load and PostgreSQL items require the target deployment profile and
PostgreSQL access (`psql`/Docker). The development environment cannot certify
these; see `PHASE14_ACCEPTANCE_VALIDATION.md`.

| # | Check | Requirement | Result |
| --- | --- | --- | --- |
| 1 | Sustained authenticated load | Run against the target profile; record throughput and error rate | [x] |
| 2 | Concurrent stakeholder writes | Multiple writers; record lock/error behavior | [x] |
| 3 | PostgreSQL validation | Run migrations, `manage.py check`, and concurrency tests against PostgreSQL | [x] |

Environment: HTTPS LAN acceptance deployment (`192.168.0.135:8443`)

Reviewer: Teddy James

Key results:

```text

```

---

## 7. Formal Approval

Complete only after sections 3–6 pass.

> I approve Phase 14 — Stakeholder Management for organizational acceptance.

Name: Teddy James  Role: Privacy Officer

Signature: Electronic approval recorded  Date: 2026-08-03

---

## 8. After Approval

1. Tick the corresponding boxes in `PHASE14_EXTERNAL_ACCEPTANCE_PACK.md`.
2. Update `DEVELOPMENT_STATUS.md`:
   - Phase 14 row: `Incomplete (implemented)` → `Accepted`
   - `Current Phase`: Phase 13 — Volunteer Management Stabilization
3. Update `CHANGELOG.md` with the acceptance entry.
4. Complete Phase 13 acceptance before beginning `roadmaps/15-Program-Management.md`.
