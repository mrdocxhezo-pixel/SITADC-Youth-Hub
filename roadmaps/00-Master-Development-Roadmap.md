# SITADC YOUTH HUB WEB APPLICATION

## FULL MASTER DEVELOPMENT PROMPT

You are a senior:

* Python software engineer
* Django full-stack developer
* Software architect
* Database architect
* Cybersecurity engineer
* DevOps engineer
* UI/UX designer
* Accessibility specialist
* Quality-assurance engineer
* Records-management specialist
* Organizational-development specialist
* Program and project-management specialist
* Monitoring, Evaluation, Accountability and Learning specialist
* Reporting and analytics specialist
* Data-protection and safeguarding specialist

Your task is to design, develop, test, document, and prepare for deployment a complete, secure, scalable, configurable, responsive, accessible, and production-ready organizational management web application called:

# SITADC Youth Hub

The application must be developed completely from scratch for:

**Sustainable Initiatives Through Transformative Actions for Development in Communities — SITADC Youth Organization.**

The SITADC Youth Hub must serve as the organization’s official digital platform for:

* Organizational administration
* Leadership management
* Membership management
* Volunteer management
* Program management
* Project management
* Stakeholder management
* Partner management
* Sponsor management
* Donor management
* Beneficiary management
* Monitoring and evaluation
* Accountability and feedback
* Organizational learning
* Reporting
* Document and records management
* Governance
* Risk management
* Safeguarding
* Compliance
* Finance
* Resource mobilization
* Communication
* Collaboration
* Decision support
* Performance monitoring
* Audit logging

The system must function as one interconnected organizational platform and not as a collection of disconnected pages.

All modules must share common:

* Users
* Roles
* Permissions
* Organizational units
* Reporting lines
* Programs
* Projects
* Activities
* Stakeholders
* Reporting periods
* Workflows
* Documents
* Notifications
* Reference numbers
* Status histories
* Audit histories

---

# 1. MANDATORY TECHNOLOGY STACK

Develop the application using only the following primary technologies:

## Backend

* Python
* Django
* Django Templates
* Django Forms
* Django ModelForms
* Django Authentication
* Django Permissions
* Django Groups
* Django ORM
* Django Class-Based Views where appropriate
* Django Function-Based Views where appropriate
* Django Middleware
* Django Signals where appropriate
* Django Management Commands
* Django Admin
* Django Sessions

## Database

* SQLite

SQLite must be used as the initial project database.

The database architecture must nevertheless follow clean relational-design principles so the application can later migrate to PostgreSQL without redesigning the entire system.

Do not use SQLite-specific shortcuts that would make future database migration unnecessarily difficult.

## Frontend

* HTML5
* CSS3
* Bootstrap 5
* Vanilla JavaScript
* Django Template Language
* Bootstrap Icons or another locally managed professional icon library

## Optional Supporting Python Libraries

Use reliable, actively maintained libraries where necessary for:

* PDF generation
* DOCX generation
* Excel generation
* Image processing
* File validation
* Two-factor authentication
* QR-code generation
* Data import and export
* Charts
* Background task preparation
* Testing
* Security checking

Every added package must be:

* Necessary
* Documented
* Version-pinned
* Compatible with the selected Python and Django versions
* Reviewed for security and licensing

## Prohibited Technology Replacements

Do not replace the required stack with:

* React
* Next.js
* Angular
* Vue
* Svelte
* Laravel
* Ruby on Rails
* Firebase
* Supabase
* MongoDB
* Node.js as the primary backend
* WordPress
* Another frontend or backend framework

JavaScript may be used for progressive enhancement, interactivity, autosave, dynamic forms, charts, filtering, previews, and asynchronous requests, but Django must remain the primary application framework.

---

# 2. DEVELOPMENT STARTING CONDITION

Assume the project starts from an empty project directory.

Create the complete project structure, including:

* Django project
* Modular Django applications
* Templates
* Static files
* Media storage
* Configuration
* Environment-variable handling
* Requirements files
* Testing structure
* Documentation
* Development scripts
* Seed data
* Database migrations
* Deployment configuration
* Security configuration

Before writing implementation code:

1. Read `AGENTS.md`.
2. Read `README.md`.
3. Read all development-roadmap Markdown files.
4. Identify the active development phase.
5. Identify dependencies on earlier phases.
6. Inspect the existing project structure.
7. Do not duplicate existing functionality.
8. Preserve valid completed work.
9. Report conflicts before replacing major architecture.
10. Follow the naming, security, testing, and documentation standards defined by the project.

If these files do not exist, create them before major implementation begins.

---

# 3. PROJECT VISION

Create a digital organizational headquarters for SITADC Youth Organization.

The system must replace fragmented processes involving:

* Spreadsheets
* Paper forms
* Email threads
* Messaging applications
* Unstructured file storage
* Manual approval processes
* Disconnected reports
* Untracked assignments
* Unstructured registers

The platform must improve:

* Accountability
* Transparency
* Organizational coordination
* Data quality
* Evidence-based decision-making
* Reporting compliance
* Institutional memory
* Program performance
* Leadership performance
* Volunteer management
* Stakeholder engagement
* Document control
* Governance
* Security
* Continuous improvement

---

# 4. PRIMARY SYSTEM OBJECTIVES

The SITADC Youth Hub must enable authorized users to:

* Create organizational records
* Update authorized records
* Complete reports
* Complete registers
* Save drafts
* Resume incomplete work
* Autosave eligible forms
* Submit records for review
* Review submitted records
* Add section-level comments
* Add general comments
* Request additional information
* Return records for correction
* Resubmit corrected records
* Recommend records for approval
* Approve records
* Reject records
* Archive records
* Restore archived records
* Track deadlines
* Track reporting compliance
* Track organizational performance
* Manage leaders
* Manage members
* Manage volunteers
* Manage programs
* Manage projects
* Manage activities
* Manage tasks
* Manage beneficiaries
* Manage partners
* Manage donors
* Manage sponsors
* Manage stakeholders
* Manage organizational documents
* Manage indicators
* Manage monitoring visits
* Manage evaluations
* Manage accountability records
* Manage meetings
* Manage events
* Manage calendars
* Generate dashboards
* Generate reports
* Export authorized data
* Maintain immutable audit histories
* Protect confidential information
* Support organizational learning
* Support continuous improvement

---

# 5. CORE ARCHITECTURAL PRINCIPLES

Build the system using the following principles:

## 5.1 Modular Architecture

Use separate Django applications for major domains while maintaining shared core services.

Recommended Django applications include:

* `core`
* `accounts`
* `organizations`
* `permissions`
* `leadership`
* `memberships`
* `volunteers`
* `stakeholders`
* `programs`
* `projects`
* `beneficiaries`
* `meal`
* `reports`
* `workflows`
* `documents`
* `meetings`
* `calendar_events`
* `notifications`
* `registers`
* `finance`
* `communications`
* `governance`
* `risk_compliance`
* `safeguarding`
* `audit`
* `search`
* `exports`
* `dashboard`
* `configuration`

Adjust this structure only when a clearer modular design is justified.

## 5.2 Separation of Concerns

Separate:

* Models
* Forms
* Views
* Services
* Selectors or query services
* Permissions
* Validators
* Utilities
* Workflows
* Export logic
* Notifications
* Audit logging
* Templates
* Static assets
* Tests

Do not place complex business logic directly inside templates or oversized views.

## 5.3 Reusable Shared Services

Create reusable services for:

* Reference-number generation
* Permission evaluation
* Scope filtering
* Status transitions
* Workflow actions
* Notifications
* Audit logging
* File validation
* Export generation
* Search
* Date and reporting-period calculations
* Soft deletion
* Archiving
* Versioning
* Approval locking

## 5.4 Migration-Ready Design

Although SQLite is required initially:

* Use normalized relational models.
* Use Django ORM.
* Avoid handwritten database-specific SQL unless strictly necessary.
* Use transactions for critical operations.
* Avoid assumptions that only work in SQLite.
* Prepare the application for future PostgreSQL migration.

---

# 6. USER REGISTRATION AND AUTHENTICATION

Implement secure authentication using Django’s authentication framework.

Support:

* Login
* Logout
* Invitation-based registration
* Account application
* Administrator approval
* Email verification where email delivery is configured
* Forgot-password workflow
* Password reset
* Password-change workflow
* Secure sessions
* Session expiry
* Device-session visibility where practical
* Account suspension
* Account deactivation
* Failed-login tracking
* Optional two-factor authentication
* Optional one-time password verification
* Secure remember-me behavior
* Login audit history

A newly registered user must not gain organizational access until an authorized administrator:

1. Reviews the application.
2. Approves the account.
3. Assigns a role.
4. Assigns an organizational scope.
5. Assigns a reporting line where applicable.
6. Activates the account.

Do not use open public registration without approval.

---

# 7. USER PROFILE REQUIREMENTS

Every user profile must support:

* Unique SITADC user ID
* Profile photograph
* First name
* Middle name
* Last name
* Preferred name
* Gender where voluntarily provided and permitted
* Date of birth where required
* Email
* Phone number
* Alternative phone number
* Physical address
* Country
* Province or region
* District
* Community
* Biography
* Skills
* Interests
* Emergency contact where applicable
* Role
* Position
* Directorate
* Department
* Team
* Supervisor
* Account status
* Date joined
* Last login
* Communication preferences
* Privacy preferences
* Uploaded documents
* Audit history

Protect sensitive personal information with strict permission checks.

---

# 8. ROLE-BASED ACCESS CONTROL

Implement Django-based role and permission management.

Use:

* Django permissions
* Django groups
* Custom application permissions
* Object ownership checks
* Organizational-scope checks
* Assignment-based checks
* Confidentiality checks
* Role-aware query filtering
* Service-layer authorization
* View-level authorization
* Template-level presentation controls

Hiding a menu item is not sufficient security.

Every protected operation must be validated on the server.

Recommended roles include:

* Super Administrator
* System Administrator
* Board Chairperson
* Board Secretary
* Board Member
* President
* Vice President
* Executive Director
* Executive Secretary
* Secretary General
* National Executive Committee Member
* Director
* Deputy Director
* Regional Coordinator
* District Coordinator
* Community Coordinator
* Team Leader
* Program Manager
* Project Manager
* Project Officer
* MEAL Officer
* Finance Officer
* Membership Officer
* Volunteer Officer
* Communications Officer
* Training Officer
* Research Officer
* Partnerships Officer
* Resource Mobilization Officer
* Quality Assurance Officer
* Safeguarding Officer
* Legal and Governance Officer
* Staff Member
* Volunteer
* Member
* Partner Representative
* Donor Representative
* Sponsor Representative
* Stakeholder Representative
* Auditor
* Read-Only User

Administrators must be able to:

* Create roles
* Edit roles
* Deactivate roles
* Assign permissions
* Clone roles
* Assign users
* Define scope levels
* Review permission histories

Prevent privilege escalation.

---

# 9. ACCESS SCOPES

Support access scopes such as:

* Own records
* Assigned records
* Team records
* Community records
* District records
* Regional records
* Department records
* Directorate records
* Program records
* Project records
* Partner-shared records
* National records
* Confidential records
* Explicitly shared records
* Administrator-wide access

Create reusable permission functions that evaluate:

* Current user
* Current role
* Assigned permissions
* Organizational unit
* Geographic scope
* Program assignment
* Project assignment
* Record ownership
* Workflow assignment
* Confidentiality
* Explicit sharing
* Administrative override

Apply scope filtering to every protected query.

Never return unauthorized objects and then merely hide them in the template.

---

# 10. ORGANIZATIONAL STRUCTURE

Implement configurable hierarchical organizational structures.

Support:

* National organization
* General Assembly
* Board of Trustees
* National Executive Committee
* Executive Management
* Directorates
* Departments
* Units
* Regions
* Districts
* Communities
* Teams
* Programs
* Projects
* Committees
* Working groups

Support:

* Parent-child relationships
* Organizational-unit types
* Active and inactive units
* Unit leadership
* Reporting lines
* Effective dates
* Historical records
* Geographic assignments
* Program assignments
* Position assignments

Recommended reporting hierarchy:

Volunteer
→ Team Leader
→ Community Coordinator
→ District Coordinator
→ Regional Coordinator
→ Directorate
→ Executive Director or Executive Secretary
→ National Executive Committee
→ Board of Trustees
→ General Assembly

Reporting lines must be configurable and must not be permanently hard-coded.

---

# 11. EXECUTIVE DIRECTORATES

Configure the following recommended directorates:

1. Directorate of Programs and Project Management
2. Directorate of Monitoring, Evaluation, Accountability and Learning
3. Directorate of Operations and Administration
4. Directorate of Finance and Resource Management
5. Directorate of Human Resources and Organizational Development
6. Directorate of Membership and Volunteer Services
7. Directorate of Partnerships, Resource Mobilization and External Relations
8. Directorate of Communications, Media and Public Relations
9. Directorate of Information and Communication Technology and Digital Innovation
10. Directorate of Research, Innovation and Knowledge Management
11. Directorate of Training and Capacity Development
12. Directorate of Governance, Legal Affairs and Compliance
13. Directorate of Quality Assurance, Risk and Safeguarding
14. Directorate of Stakeholder Engagement and Community Relations
15. Directorate of Events, Protocol and Special Initiatives
16. Directorate of Enterprise Development and Sustainability

Administrators must be able to:

* Add directorates
* Edit directorates
* Merge directorates
* Deactivate directorates
* Archive directorates
* Assign directors
* Assign departments
* Update reporting relationships
* View historical changes

---

# 12. DEPARTMENTS

Configure departments including:

* Executive Office
* Operations
* Programs
* Project Management
* MEAL
* Finance and Administration
* Human Resources
* Membership and Volunteer Management
* Partnerships and Resource Mobilization
* Communications and Public Relations
* Information and Communication Technology
* Research, Innovation and Knowledge Management
* Training and Capacity Development
* Stakeholder Relations
* Document and Records Management
* Quality Assurance and Compliance
* Safeguarding, Ethics and Accountability
* Legal and Governance
* Events and Protocol
* Business Development and Sustainability

Administrators must be able to configure:

* Department names
* Codes
* Descriptions
* Directorate ownership
* Department heads
* Parent units
* Status
* Reporting relationships
* Effective dates
* Associated permissions
* Programs
* Projects
* Staff
* Leaders

---

# 13. IDENTIFICATION AND REFERENCE NUMBERING SYSTEM

Every applicable entity must receive an automatically generated, unique, non-reusable reference number.

Use a configurable format such as:

`SITADC-{PREFIX}-{YEAR}-{SEQUENCE}`

Examples:

* User: `SITADC-USR-2026-00001`
* Leader: `SITADC-LDR-2026-00001`
* Member: `SITADC-MBR-2026-00001`
* Volunteer: `SITADC-VOL-2026-00001`
* Program: `SITADC-PRG-2026-00001`
* Project: `SITADC-PRJ-2026-00001`
* Activity: `SITADC-ACT-2026-00001`
* Task: `SITADC-TSK-2026-00001`
* Beneficiary: `SITADC-BEN-2026-00001`
* Partner: `SITADC-PTN-2026-00001`
* Sponsor: `SITADC-SPN-2026-00001`
* Donor: `SITADC-DNR-2026-00001`
* Indicator: `SITADC-IND-2026-00001`
* Report: `SITADC-RPT-2026-00001`
* Document: `SITADC-DOC-2026-00001`
* Policy: `SITADC-POL-2026-00001`
* MoU: `SITADC-MOU-2026-00001`
* Meeting: `SITADC-MTG-2026-00001`
* Agreement: `SITADC-AGR-2026-00001`
* Risk: `SITADC-RSK-2026-00001`
* Complaint: `SITADC-CMP-2026-00001`
* Incident: `SITADC-INC-2026-00001`

Requirements:

* Generate numbers server-side.
* Use database transactions.
* Prevent duplicate sequences.
* Never reuse identifiers.
* Do not recycle deleted draft numbers.
* Do not reassign archived record numbers.
* Record manual changes.
* Require special permission for manual changes.
* Require a written reason for manual changes.
* Preserve previous identifiers in immutable history.
* Include identifiers in profiles, exports, registers, reports, audit logs, and generated documents.
* Allow configuration of prefixes.
* Allow configuration of digit length.
* Allow configuration of annual or continuous reset rules.
* Allow configuration by entity type.

Implement a `NumberingConfiguration` model and a transaction-safe sequence-generation service.

Because SQLite does not provide the same row-locking behavior as enterprise databases, design the generator carefully using atomic transactions, uniqueness constraints, retries, and tests for concurrent requests.

---

# 14. DASHBOARD ARCHITECTURE

Create separate role-aware dashboard experiences for:

* Super administrators
* System administrators
* Board members
* Executive management
* Management
* Directors
* Coordinators
* Staff
* Volunteers
* Members
* Partners
* Sponsors
* Donors
* Stakeholders
* MEAL officers
* Finance officers
* Reviewers
* Approvers

The main dashboard must display relevant authorized information such as:

* User greeting
* Profile photograph
* User role
* Position
* Organizational unit
* SITADC user ID
* Reports due
* Reports overdue
* Draft reports
* Submitted reports
* Reports under review
* Returned reports
* Approved reports
* Pending approvals
* Pending reviews
* Upcoming deadlines
* Recent submissions
* Recent approvals
* Notifications
* Quick actions
* Program progress
* Project progress
* Volunteer statistics
* Leader statistics
* Stakeholder statistics
* Beneficiary reach
* Indicator performance
* Document status
* Expiring documents
* Calendar preview
* Performance summaries
* Organizational statistics

Dashboard data must come from the database.

Do not use hard-coded demonstration arrays in production functionality.

Apply:

* Role filtering
* Scope filtering
* Date filtering
* Reporting-period filtering
* Efficient aggregation
* Pagination where appropriate
* Accessible summaries
* Table alternatives for charts

---

# 15. APPLICATION NAVIGATION

## Mobile Bottom Navigation

Use:

* Home
* Reports
* Calendar
* Notifications
* Profile

## Desktop Sidebar and Mobile Menu

Use the following order:

1. Dashboard
2. Leaders
3. Volunteers
4. Programs
5. Partners
6. Sponsors
7. Donors
8. Registers
9. Dashboards
10. Documents
11. Reviews
12. Approvals
13. Settings
14. Audit Logs
15. Help and Support
16. About SITADC

Only display destinations the current user can access.

Navigation must:

* Remain consistent
* Identify the active page
* Collapse on smaller screens
* Support keyboard navigation
* Support screen readers
* Display notification counts
* Include profile access
* Include secure sign-out
* Support light and dark modes
* Preserve user context where appropriate

---

# 16. REPORT MANAGEMENT MODULE

Create a complete report-management system.

Users must be able to:

* Browse report categories
* Browse templates
* Search templates
* Filter templates
* Create reports
* Complete structured forms
* Save drafts
* Autosave
* Resume drafts
* Preview reports
* Validate reports
* Submit reports
* Resubmit returned reports
* Duplicate authorized reports
* Archive reports
* Restore archived reports
* View report history
* Export reports
* Attach evidence
* View comments
* Reply to reviewer comments
* View approval trails
* Compare versions

Report statuses must support:

Draft
→ Submitted
→ Under Review
→ Returned for Correction
→ Resubmitted
→ Recommended for Approval
→ Pending Approval
→ Approved

Alternative paths may include:

* Rejected
* Withdrawn
* Cancelled
* Archived
* Reopened under special authority

Each workflow action must record:

* Actor
* Date and time
* Previous status
* New status
* Comments
* Reason
* Version
* Assignment
* Decision
* Organizational scope
* IP address where available
* Session information where appropriate

Approved reports must be locked.

Reopening an approved report requires:

* Special permission
* Written justification
* Audit entry
* New version
* Notification to affected reviewers and approvers

---

# 17. REPORT CATEGORIES

Create configurable alphabetically grouped report categories.

## A. Organizational Governance

* Annual Organizational Report
* Governance Performance Report
* Board Meeting Minutes
* Executive Committee Minutes
* AGM Report
* Leadership Performance Report
* Policy Compliance Report
* Strategic Plan Progress Report
* Risk Management Report

## B. Leadership

* Monthly Leadership Activity Report
* Weekly Leadership Update
* Leadership Performance Scorecard
* Leadership Development Report
* Leadership Coaching and Mentorship Report
* Staff and Volunteer Supervision Report
* Team Performance Report
* Leadership Attendance Report
* Leadership Succession Progress Report
* Leadership Challenges and Recommendations Report

## C. Program Management

* Annual Program Plan
* Quarterly Program Implementation Report
* Monthly Program Progress Report
* Weekly Activity Report
* Activity Completion Report
* Project Status Report
* Program Outcome Report
* Program Impact Report
* Project Closure Report
* Beneficiary Statistics Report
* Community Engagement Report
* Lessons Learned Report

## D. Membership and Volunteer Management

* Membership Register
* Volunteer Register
* Volunteer Activity Report
* Volunteer Attendance Report
* Volunteer Performance Report
* Volunteer Training Report
* Volunteer Deployment Report
* Volunteer Recognition Report
* Volunteer Exit Report
* Volunteer Supervision Report

## E. Monitoring, Evaluation, Accountability and Learning

* Results Framework Report
* Indicator Performance Report
* Baseline Report
* Target Report
* Actual Results Report
* Monitoring Visit Report
* Evaluation Report
* Data Quality Assessment Report
* Learning Log Report
* Lessons Learned Report
* Performance Scorecard
* Accountability and Feedback Report

## F. Finance

* Annual Budget
* Monthly Financial Report
* Quarterly Financial Report
* Budget Utilization Report
* Cash Flow Report
* Expense Report
* Income Report
* Donor Fund Utilization Report
* Financial Accountability Report
* Financial Audit Report

## G. Partnerships, Sponsors and Donors

* Partner Engagement Report
* Partnership Performance Report
* Donor Report
* Sponsor Report
* Resource Mobilization Report
* Contribution Report
* MoU Performance Report
* Agreement Compliance Report
* Stakeholder Engagement Report

## H. Communications and Media

* Communications Report
* Media Coverage Report
* Social Media Performance Report
* Campaign Report
* Publication Report
* Website Analytics Report
* Visibility Report
* Public Relations Report

## I. Training and Capacity Building

* Training Plan
* Training Attendance Report
* Training Completion Report
* Training Evaluation Report
* Capacity Assessment Report
* Mentorship Report
* Coaching Report
* Skills Development Report

## J. Meetings and Events

* Meeting Agenda
* Meeting Minutes
* Action Tracker
* Decision Register
* Event Plan
* Event Report
* Attendance Register
* Event Evaluation Report

## K. Safeguarding and Protection

* Safeguarding Report
* Safeguarding Incident Report
* Referral Report
* Child Protection Report
* Safeguarding Risk Assessment
* Safeguarding Compliance Report

## L. Administration and Operations

* Administrative Report
* Procurement Report
* Asset Report
* Logistics Report
* Office Operations Report
* Inventory Report
* Travel Report
* Maintenance Report

## M. Quality Assurance

* Internal Quality Assessment
* Compliance Checklist
* Process Audit Report
* Service Quality Report
* Corrective Action Report
* Continuous Improvement Report

## N. Risk and Compliance

* Risk Register
* Incident Report
* Safeguarding Report
* Complaints Register
* Whistleblower Report
* Ethics Report
* Compliance Report

Apply stricter access controls to:

* Safeguarding reports
* Whistleblower reports
* Complaint records
* Incident reports
* Ethics reports
* Personnel-related reports
* Financial investigations

## O. Organizational Learning

* After Action Review
* Reflection Meeting Report
* Lessons Learned Report
* Good Practice Report
* Innovation Report
* Organizational Learning Report
* Adaptation Decision Report

## P. Organizational Registers

* Membership Register
* Volunteer Register
* Beneficiary Register
* Training Register
* Attendance Register
* Stakeholder Register
* Donor Register
* Partner Register
* Asset Register
* Risk Register
* Issue Register
* Complaints Register
* Action Tracker
* Decision Register
* Lessons Learned Register
* Innovation Register
* Policy Register
* Meeting Register
* Event Register
* Media Register
* Grant Register
* Proposal Register

Administrators must be able to:

* Add categories
* Edit categories
* Reorder categories
* Deactivate categories
* Archive categories
* Add templates
* Edit templates
* Version templates
* Deactivate templates
* Archive templates
* Assign permissions
* Assign workflows
* Assign frequencies

---

# 18. DYNAMIC REPORT TEMPLATE BUILDER

Create a configurable report-template builder.

Supported field types must include:

* Short text
* Long text
* Rich text
* Integer
* Decimal
* Currency
* Percentage
* Date
* Time
* Date range
* Dropdown
* Multi-select
* Radio
* Checkbox
* Yes or no
* User selector
* Organizational-unit selector
* Program selector
* Project selector
* Activity selector
* Partner selector
* Location selector
* Indicator selector
* Repeating table
* File upload
* Image upload
* Signature
* Calculated field
* Read-only system field

Support:

* Required fields
* Field validation
* Conditional display
* Conditional requirements
* Section ordering
* Field ordering
* Repeating rows
* Instructions
* Help text
* Placeholder text
* Default values
* Formula fields
* Template versioning
* Workflow assignment
* Reporting frequency
* Responsible role
* Reviewer role
* Approver role
* Confidentiality level
* Export layout
* Signature requirements
* Evidence requirements
* Deadline rules

Historical reports must continue to use the exact template version under which they were created.

Never silently apply a newer template structure to an already submitted historical report.

---

# 19. REVIEW AND APPROVAL WORKSPACES

Create separate Review and Approval modules.

## Reviewers Must Be Able To

* View assigned reports
* Preview complete submissions
* Add section comments
* Add general comments
* Request additional information
* Return for correction
* Recommend approval
* Reject where permitted
* Compare versions
* Record decisions
* View deadlines
* View overdue assignments
* View submission history

## Approvers Must Be Able To

* View recommended reports
* View submission histories
* View reviewer comments
* Approve
* Reject
* Return for correction
* Record decision reasons
* Apply digital approval details
* View overdue approvals
* View approval queues
* Delegate where authorized

Prevent:

* Unauthorized self-review
* Unauthorized self-approval
* Circular approval workflows
* Approval outside assigned scope
* Approval after permissions are revoked
* Editing approved content without reopening

---

# 20. LEADER MANAGEMENT

Create complete leader profiles containing:

* Leader ID
* User account
* Profile image
* Full name
* Contact information
* Position
* Directorate
* Department
* Region
* District
* Community
* Team
* Reporting line
* Appointment date
* Term start date
* Term end date
* Responsibilities
* Assigned programs
* Assigned projects
* Targets
* Attendance
* Submitted reports
* Review completion
* Approval responsibilities
* Performance scorecard
* Coaching history
* Mentorship history
* Training history
* Performance reviews
* Succession readiness
* Status
* Documents
* Position history
* Audit history

Support:

* Leader directories
* Profile tabs
* Filters
* Exports
* Assignments
* Transfers
* Acting appointments
* Status changes
* Term renewals
* Historical position records
* Performance reviews
* Succession planning

---

# 21. MEMBERSHIP AND VOLUNTEER MANAGEMENT

Create complete member and volunteer lifecycle management.

Volunteer profiles must include:

* Volunteer ID
* Profile photograph
* Full name
* Contact details
* Emergency contact
* Skills
* Interests
* Availability
* Location
* Region
* District
* Community
* Assigned team
* Assigned program
* Assigned project
* Assigned activity
* Supervisor
* Deployment history
* Attendance
* Training
* Performance
* Recognition
* Warnings
* Safeguarding compliance
* Documents
* Exit information
* Status
* Audit history

Support:

* Registration
* Screening
* Approval
* Orientation
* Assignment
* Deployment
* Attendance
* Supervision
* Training
* Performance assessment
* Recognition
* Warning
* Suspension
* Exit
* Re-engagement
* Transfer
* Volunteer history

Protect personal and identification information.

---

# 22. STAKEHOLDER, PARTNER, SPONSOR AND DONOR MANAGEMENT

Use one reusable stakeholder architecture with specialized views.

Support stakeholder types including:

* Partners
* Sponsors
* Donors
* Government institutions
* Educational institutions
* Technology organizations
* NGOs
* Civil-society organizations
* Community organizations
* Development partners
* Media organizations
* Training institutions
* Consultants
* Vendors
* Networks
* Private-sector organizations
* Academic institutions

Stakeholder profiles must include:

* Stakeholder ID
* Organization name
* Logo
* Tagline
* Description
* Stakeholder type
* Contact persons
* Phone
* Email
* Website
* Social links
* Address
* Geographic coverage
* Areas of interest
* Agreement type
* MoUs
* Agreements
* Start date
* End date
* Contributions
* Funding
* In-kind support
* Programs supported
* Projects supported
* Engagement history
* Reports shared
* Commitments
* Outstanding actions
* Performance
* Renewal reminders
* Due diligence
* Confidential documents
* Status
* Audit history

Partner, donor, sponsor, and stakeholder representatives must only access records explicitly shared with them.

---

# 23. PROGRAM AND PROJECT MANAGEMENT

Support the operational hierarchy:

Organization
→ Program
→ Project
→ Workstream
→ Activity
→ Task
→ Deliverable
→ Evidence

Support the results hierarchy:

Strategic Goal
→ Program Goal
→ Objective
→ Output
→ Activity
→ Indicator
→ Target
→ Actual Result
→ Outcome
→ Impact

## Program Profiles

Include:

* Program ID
* Program title
* Program type
* Description
* Problem statement
* Rationale
* Goal
* Objectives
* Outputs
* Outcomes
* Expected impact
* Theory of change
* Results framework
* Start date
* End date
* Geographic coverage
* Target beneficiaries
* Responsible directorate
* Program manager
* Team
* Partners
* Donors
* Sponsors
* Budget
* Funding
* Indicators
* Risks
* Sustainability
* Safeguarding
* Status
* Documents
* Reports
* Lessons learned

## Project Profiles

Include:

* Project ID
* Project title
* Parent program
* Project type
* Description
* Objectives
* Scope
* Activities
* Tasks
* Deliverables
* Indicators
* Outputs
* Outcomes
* Timeline
* Milestones
* Dependencies
* Team
* Partners
* Beneficiaries
* Budget
* Funding
* Risks
* Issues
* Evidence
* Progress
* Reports
* Lessons learned
* Closure
* Status

Support:

* Project planning
* Work plans
* Activity tracking
* Task tracking
* Deliverables
* Milestones
* Timelines
* Budgets
* Team assignments
* RACI matrices
* Beneficiary planning
* Risk registers
* Issue registers
* Evidence
* Progress updates
* Change requests
* Project closure
* Program evaluation
* Portfolio dashboards

---

# 24. BENEFICIARY MANAGEMENT

Create secure beneficiary-management functionality.

Support:

* Beneficiary IDs
* Registration
* Demographic information
* Program participation
* Project participation
* Activity participation
* Consent
* Safeguarding requirements
* Attendance
* Services received
* Outcomes
* Follow-up
* Referrals
* Evidence
* Exit
* Duplicate detection
* Privacy controls

Beneficiary-level information must be strongly restricted.

Dashboards and exports should use aggregated statistics wherever possible.

Implement small-group suppression so reports do not indirectly reveal identities through very small statistical groups.

---

# 25. MONITORING, EVALUATION, ACCOUNTABILITY AND LEARNING

Create a complete MEAL module supporting:

Strategic priorities
→ Results frameworks
→ Objectives
→ Indicators
→ Baselines
→ Targets
→ Data collection plans
→ Data collection
→ Verification
→ Actual results
→ Performance analysis
→ Monitoring visits
→ Evaluations
→ Data-quality assessments
→ Accountability and feedback
→ Learning
→ Corrective actions
→ Scorecards
→ Management decisions
→ Continuous improvement

## Results Frameworks

Support:

* Strategic frameworks
* Program frameworks
* Project frameworks
* Logical frameworks
* Results chains
* Theories of change
* Performance measurement frameworks
* Donor-specific frameworks

## Results Hierarchy

Impact
→ Long-term Outcome
→ Intermediate Outcome
→ Immediate Outcome
→ Output
→ Activity
→ Input

## Indicator Types

Support:

* Impact
* Outcome
* Output
* Process
* Activity
* Input
* Financial
* Compliance
* Quality
* Reach
* Participation
* Satisfaction
* Capacity
* Sustainability

## Indicator Metadata

Include:

* Indicator ID
* Name
* Definition
* Type
* Result level
* Program
* Project
* Formula
* Numerator
* Denominator
* Unit
* Baseline
* Target
* Data source
* Collection method
* Collection frequency
* Reporting frequency
* Responsible officer
* Verification officer
* Disaggregation
* Data-quality requirements
* Confidentiality
* Limitations
* Means of verification

## Baselines

Support versioned baseline records with:

* Evidence
* Verification
* Review
* Approval
* Effective date
* Revision history

## Targets

Support:

* Overall targets
* Annual targets
* Quarterly targets
* Monthly targets
* Geographic targets
* Beneficiary-group targets
* Partner targets
* Team targets
* Program targets
* Project targets

## Actual Results

Support:

* Reporting period
* Target
* Actual
* Cumulative target
* Cumulative actual
* Achievement percentage
* Variance
* Disaggregation
* Evidence
* Quality status
* Verification
* Approval
* Locking

## Calculations

Support:

* Count
* Sum
* Average
* Median
* Percentage
* Rate
* Ratio
* Difference
* Cumulative total
* Unique beneficiary count
* Weighted score
* Index
* Formula-based result
* Narrative result

Protect against:

* Division by zero
* Duplicate results
* Double counting
* Invalid periods
* Missing denominators
* Incompatible units
* Invalid negative values
* Inconsistent disaggregation totals

## Monitoring

Support:

* Monitoring plans
* Monitoring visits
* Monitoring checklists
* Findings
* Recommendations
* Corrective actions
* Follow-ups
* Evidence
* Monitoring reports

## Evaluations

Support:

* Baseline evaluations
* Formative evaluations
* Process evaluations
* Midterm evaluations
* Outcome evaluations
* Impact evaluations
* Endline evaluations
* Final evaluations
* Internal evaluations
* External evaluations
* Participatory evaluations
* Sustainability evaluations
* Cost-effectiveness evaluations

Include:

* Terms of reference
* Evaluation questions
* Methodology
* Sampling
* Teams
* Findings
* Conclusions
* Recommendations
* Management responses
* Recommendation tracking
* Dissemination

## Data-Quality Assessments

Support:

* Accuracy
* Completeness
* Timeliness
* Consistency
* Reliability
* Validity
* Integrity
* Precision
* Uniqueness
* Accessibility
* Confidentiality
* Traceability

## Learning

Support:

* Learning logs
* Reflection meetings
* After-action reviews
* Learning workshops
* Good practices
* Lessons learned
* Adaptation decisions
* Learning actions
* Knowledge sharing

## Performance Scorecards

Support:

* Organizational scorecards
* Strategic-plan scorecards
* Program scorecards
* Project scorecards
* Directorate scorecards
* Department scorecards
* Regional scorecards
* District scorecards
* Community scorecards
* Team scorecards
* Partner scorecards
* Leadership scorecards
* Volunteer scorecards
* MEAL compliance scorecards

Allow configurable:

* Indicators
* Weights
* Formulas
* Performance bands
* Evidence
* Review
* Approval

---

# 26. ACCOUNTABILITY AND FEEDBACK

Support:

* Beneficiary feedback
* Community feedback
* Complaints
* Suggestions
* Compliments
* Partner feedback
* Staff feedback
* Volunteer feedback
* Safeguarding referrals
* Whistleblower submissions

Fields must include:

* Reference number
* Source
* Program
* Project
* Location
* Date received
* Category
* Description
* Confidentiality
* Consent
* Assigned owner
* Response deadline
* Action
* Resolution
* Closure
* Status

Apply restricted workflows to:

* Safeguarding cases
* Whistleblower submissions
* Sensitive complaints
* Abuse allegations
* Child-protection cases
* Sexual exploitation or harassment cases

Never expose complainant identities to unauthorized users.

---

# 27. DOCUMENT AND RECORDS MANAGEMENT

Create an enterprise document-management module.

Document lifecycle:

Creation or upload
→ Classification
→ Metadata completion
→ Ownership assignment
→ Confidentiality assignment
→ Review
→ Revision
→ Approval
→ Publication or controlled sharing
→ Active use
→ Version update
→ Expiry review
→ Renewal or replacement
→ Archival
→ Retention
→ Authorized disposal

Support:

* Single upload
* Multiple upload
* Drag and drop
* Upload progress
* File validation
* Duplicate detection
* Categories
* Types
* Tags
* Ownership
* Confidentiality
* Version control
* Preview
* Download
* Review
* Approval
* Expiry
* Renewal
* Retention
* Archival
* Controlled disposal
* Search
* Saved searches
* Favorites
* Recently viewed
* Sharing
* Secure access links
* Watermarks
* Audit logs

Use shared entities such as:

* `Document`
* `DocumentVersion`
* `DocumentCategory`
* `DocumentType`
* `DocumentTag`
* `DocumentRelationship`
* `DocumentApproval`
* `DocumentAccessRule`

Documents may link to:

* Organizational units
* Programs
* Projects
* Activities
* Leaders
* Volunteers
* Stakeholders
* Agreements
* MoUs
* Meetings
* Reports
* Policies
* Indicators
* Monitoring visits
* Evaluations
* Risks
* Audits
* Trainings
* Events

Approved document versions must never be overwritten.

Every replacement must create a new version.

---

# 28. FILE STORAGE ARCHITECTURE

Use Django’s storage abstraction.

Support:

* Local development storage
* Configurable production media storage
* Future object-storage integration
* Private file access
* File metadata
* Checksums
* Storage quotas
* Versioned files
* Secure downloads

Do not serve confidential files through unrestricted public media URLs.

Protected downloads must pass through authenticated, permission-checked Django views or another secure storage mechanism.

Recommended storage path:

`organization/category/year/document-reference/version/file`

Example:

`SITADC/policies/2026/SITADC-POL-2026-00001/v1.0/policy.pdf`

The database must remain the source of truth for:

* Document identity
* Metadata
* Version
* Owner
* Status
* Permissions
* Relationships
* Storage path
* Checksum
* File size
* MIME type
* Confidentiality
* Retention

Validate files using:

* Extension
* MIME type
* File signature where practical
* File size
* Filename length
* Filename characters
* Checksum
* Duplicate-content checks

Support configurable formats including:

* PDF
* DOC
* DOCX
* XLS
* XLSX
* CSV
* PPT
* PPTX
* TXT
* RTF
* JPG
* JPEG
* PNG
* WEBP
* Sanitized SVG
* MP4
* MP3
* ZIP where explicitly authorized

Check for:

* Empty files
* Oversized files
* Corrupted files
* Duplicate files
* Unsupported files
* Suspicious filenames
* Spoofed MIME types
* Prohibited file types

---

# 29. MEETINGS, EVENTS AND CALENDAR

Create:

* Organizational calendar
* Reporting calendar
* Meeting calendar
* Training calendar
* Program calendar
* Project calendar
* Monitoring calendar
* Evaluation calendar
* Document-review calendar
* Agreement-renewal calendar

Meeting records must support:

* Meeting ID
* Title
* Type
* Date
* Time
* Location
* Virtual link
* Organizer
* Participants
* Agenda
* Documents
* Minutes
* Attendance
* Decisions
* Actions
* Resolutions
* Approval of minutes
* Meeting packs
* Notifications

Calendar events must only be visible to authorized users.

---

# 30. NOTIFICATIONS AND ANNOUNCEMENTS

Create notifications for real events including:

* User invitation
* Account approval
* Account rejection
* Assignment
* Report due
* Report overdue
* Report submitted
* Report returned
* Report approved
* Report rejected
* Review assigned
* Approval assigned
* Comment added
* Program milestone due
* Project task due
* Indicator reporting due
* Result verification required
* Monitoring visit scheduled
* Evaluation scheduled
* Corrective action due
* Document review due
* Document expiring
* Policy acknowledgement required
* MoU expiring
* Agreement expiring
* Meeting scheduled
* Training scheduled
* Safeguarding action assigned
* Account status change

Support:

* In-app notifications
* Optional email notifications
* Priority levels
* Read and unread status
* Reminder schedules
* Escalation
* Links to related records
* Notification preferences
* Organization-wide announcements
* Role-targeted announcements
* Unit-targeted announcements

Notification previews must not reveal restricted information.

---

# 31. CENTRALIZED REGISTERS

Create registers for:

* Membership
* Volunteers
* Beneficiaries
* Leadership
* Training
* Attendance
* Stakeholders
* Partners
* Sponsors
* Donors
* Assets
* Risks
* Issues
* Complaints
* Incidents
* Actions
* Decisions
* Lessons learned
* Innovations
* Policies
* MoUs
* Agreements
* Meetings
* Events
* Media
* Grants
* Proposals
* Documents
* Indicators
* Monitoring visits
* Evaluations
* Corrective actions

Every register must provide:

* Search
* Filtering
* Sorting
* Pagination
* Saved views
* Permission-aware columns
* Export
* Detail view
* Status filters
* Date filters
* Organizational-scope filters

---

# 32. GLOBAL SEARCH

Create permission-aware global search across:

* Users
* Leaders
* Members
* Volunteers
* Programs
* Projects
* Activities
* Partners
* Sponsors
* Donors
* Stakeholders
* Reports
* Documents
* Policies
* MoUs
* Agreements
* Meetings
* Indicators
* Monitoring visits
* Evaluations
* Registers

Support:

* Search suggestions
* Recent searches
* Saved searches
* Search history
* Filters
* Result highlighting
* Clear-search action
* Pagination

Search must never reveal:

* Unauthorized records
* Sensitive titles
* Confidential file names
* Restricted descriptions
* Hidden contact details
* Protected beneficiary identities

---

# 33. EXPORT ENGINE

Support authorized exports to:

* PDF
* DOCX
* XLSX
* CSV
* JSON where specially authorized

Exports should include, where appropriate:

* SITADC Youth Organization logo
* Organization name
* Report title
* Register title
* Record reference number
* Reporting period
* Applied filters
* Prepared by
* Reviewed by
* Approved by
* Exported by
* Export date
* Confidentiality classification
* Version number
* Approval status
* Page numbers
* Clear headings
* Data-quality status
* Signature information

Apply:

* Server-side permission checks
* Scope restrictions
* Confidentiality restrictions
* Beneficiary privacy controls
* Small-group suppression
* Watermarks
* Audit logging

Never rely solely on client-side JavaScript to export protected datasets.

---

# 34. AUDIT LOGGING

Audit important actions including:

* Login
* Logout
* Failed login
* User creation
* Invitation
* Role assignment
* Permission change
* Account suspension
* Record creation
* Record update
* Record deletion
* Record restoration
* Report submission
* Review decision
* Approval decision
* Rejection
* Return for correction
* Version creation
* File upload
* File preview
* File download
* Export
* Sharing
* Confidential-record access
* Baseline revision
* Target revision
* Actual-result verification
* Monitoring finding
* Evaluation recommendation
* Corrective action
* Document disposal
* Configuration change

Audit fields must include:

* Actor
* Action
* Entity type
* Record ID
* Previous values
* New values
* Timestamp
* Reason
* Session identifier where appropriate
* IP address where available
* User agent where available
* Result
* Organizational scope

Audit records must be immutable to ordinary users.

Do not allow standard administrators to edit or delete audit events through the normal application interface.

---

# 35. STATUS MANAGEMENT

Use configurable statuses including:

* Draft
* Incomplete
* Submitted
* Under Review
* Revision Required
* Returned
* Resubmitted
* Recommended for Approval
* Pending Approval
* Approved
* Rejected
* Active
* Inactive
* On Track
* At Risk
* Delayed
* Overdue
* Completed
* Closed
* Suspended
* Withdrawn
* Superseded
* Archived
* Cancelled

Every transition must record:

* Previous status
* New status
* Actor
* Date and time
* Reason
* Comments
* Related workflow action

Never overwrite status history.

Use a reusable status-transition service and validate allowed transitions.

---

# 36. FORM REQUIREMENTS

All forms must provide:

* Clear labels
* Required-field indicators
* Inline validation
* Server-side validation
* Accessible error summaries
* Save draft
* Resume later
* Unsaved-change warnings
* Loading states
* Success messages
* Error messages
* Permission-aware controls
* Confirmation before destructive actions
* Dependent fields
* Autosave where appropriate
* Mobile-friendly controls
* Keyboard-safe behavior

Dependent-field examples:

* Directorate filters departments.
* Region filters districts.
* District filters communities.
* Program filters projects.
* Project filters activities.
* Framework filters results.
* Result filters indicators.
* Indicator loads its formula and unit.
* Document category filters document types.
* Document type loads required metadata.
* Confidentiality displays access warnings.
* Reporting frequency generates deadlines.

Use JavaScript for progressive enhancement, but critical validation must also run on the server.

---

# 37. SECURITY REQUIREMENTS

Protect:

* User identities
* Beneficiary identities
* Contact details
* Health information
* Safeguarding records
* Complaints
* Whistleblower reports
* Financial information
* Board documents
* Personnel records
* Volunteer identification records
* Partner due-diligence records
* Evaluation datasets
* Interview notes
* Signed agreements
* Confidential evidence

Implement:

* Least privilege
* Django permission checks
* Scope-aware query filtering
* Server-side validation
* Secure password hashing
* CSRF protection
* XSS protection
* Secure cookies
* Session security
* Clickjacking protection
* Content Security Policy where practical
* HTTPS-ready configuration
* File validation
* Rate limiting where practical
* Login throttling
* Data minimization
* Consent tracking
* Soft deletion
* Retention rules
* Privacy-aware exports
* Audit logging
* Small-group suppression
* Secure error handling
* Environment variables
* Secret-key protection

Do not expose sensitive data through:

* Public media URLs
* Browser console logs
* Query strings
* Notification previews
* Unauthorized thumbnails
* Public dashboards
* Filenames
* Search suggestions
* Detailed error messages
* Client-side source code
* Unrestricted exports

Never hard-code:

* Django secret keys
* Email credentials
* Database credentials
* Storage credentials
* API keys
* Administrative passwords

---

# 38. PRIVACY AND CONFIDENTIALITY

Support confidentiality levels such as:

* Public
* Internal
* Restricted
* Confidential
* Highly Confidential
* Safeguarding Restricted
* Board Restricted
* Finance Restricted
* Personnel Restricted

Confidentiality must influence:

* Visibility
* Search
* Download
* Preview
* Export
* Sharing
* Notifications
* Dashboard summaries
* Audit requirements
* Retention
* Approval routing

Apply data minimization.

Only collect personal information that is necessary for a documented organizational purpose.

---

# 39. ACCESSIBILITY

Meet WCAG-oriented accessibility requirements.

Implement:

* Semantic HTML5
* Proper heading order
* Form labels
* ARIA attributes where needed
* Keyboard navigation
* Visible focus states
* Skip links
* Screen-reader announcements
* Accessible validation errors
* Accessible tables
* Table alternatives for visual cards
* Descriptive buttons
* Sufficient contrast
* Non-color status indicators
* Reduced-motion support
* Accessible modals
* Focus trapping
* Focus restoration
* Accessible upload progress
* Accessible charts
* Text summaries for charts

Do not communicate status using color alone.

Every status indicator must include readable text and, where useful, an icon.

---

# 40. UI AND VISUAL IDENTITY

Create a modern, professional, youthful, vibrant, trustworthy interface.

Use:

* SITADC brand colors
* Clean white surfaces
* Blue gradients
* Purple gradients
* Indigo gradients
* Cyan gradients
* Emerald success indicators
* Orange action highlights
* Red warning and error indicators
* Rounded cards
* Material Design 3-inspired principles
* Clear typography
* Accessible font sizes
* Professional icons
* Restrained animations
* Responsive layouts
* Modern forms
* Dashboard cards
* Clear status chips
* Consistent spacing
* Strong visual hierarchy

Support:

* Light mode
* Dark mode
* Desktop
* Laptop
* Tablet
* Mobile
* Small Android screens
* Large Android screens
* Keyboard navigation
* Screen readers
* High-contrast states
* Reduced-motion preferences
* Touch-friendly targets
* Responsive tables
* Accessible dialogs

Use the SITADC Youth Organization logo consistently on:

* Splash screen
* Login screen
* Main navigation
* Reports
* Exported documents
* Certificates
* About page

Use a placeholder logo until the official asset is supplied.

---

# 41. RESPONSIVE DESIGN

Use Bootstrap breakpoints thoughtfully.

Do not simply shrink desktop layouts.

For small screens:

* Convert complex data tables into cards where appropriate.
* Use horizontal scrolling only when necessary.
* Keep primary actions reachable.
* Use sticky bottom navigation where appropriate.
* Collapse secondary filters.
* Use full-screen mobile dialogs where appropriate.
* Preserve accessible labels.
* Avoid text clipping.
* Ensure touch-friendly controls.
* Keep forms keyboard-safe.
* Stack dashboard cards appropriately.

---

# 42. PERFORMANCE

Implement:

* Pagination
* Lazy loading
* Debounced search
* Indexed database fields
* Efficient ORM queries
* `select_related`
* `prefetch_related`
* Limited column selection
* Cached configuration lists
* Optimized dashboard queries
* Upload progress
* Loading skeletons
* Image optimization
* Thumbnail generation where appropriate
* Timeout handling
* Graceful error recovery
* Query-count testing for critical screens

Do not load entire large tables into the browser.

Avoid N+1 query problems.

---

# 43. DATABASE DESIGN

Use:

* UUID or stable internal primary keys where appropriate
* Human-readable reference numbers as separate unique fields
* Foreign keys
* Many-to-many relationships
* Through models where relationship metadata is required
* Unique constraints
* Check constraints where supported
* Database indexes
* Created and updated timestamps
* Created-by and updated-by fields where appropriate
* Soft-delete fields
* Archive fields
* Effective dates
* Version fields
* Status history tables
* Assignment history tables

Avoid:

* Duplicated text where relationships should be used
* Giant single models containing unrelated domains
* Unstructured JSON for core relational records
* Hard-coded organizational names
* Hard-coded workflow rules
* Hard-coded permission logic scattered across views

JSON fields may be used only where genuinely appropriate, such as dynamic template responses, and must still be validated against the corresponding template definition.

---

# 44. CONFIGURATION MANAGEMENT

Administrators must be able to configure:

* Organization profile
* Logo
* Brand settings
* Directorates
* Departments
* Organizational units
* Positions
* Roles
* Permissions
* Statuses
* Reporting periods
* Reporting frequencies
* Report categories
* Report templates
* Workflows
* Confidentiality levels
* File types
* File-size limits
* Numbering formats
* Notification rules
* Reminder schedules
* Escalation rules
* Retention periods
* Dashboard settings
* Export settings
* Email settings
* System-maintenance settings

Configuration changes must be audited.

---

# 45. TESTING STRATEGY

Write comprehensive tests.

## Unit Tests

Test:

* Models
* Managers
* Services
* Validators
* Forms
* Permission functions
* Reference-number generation
* Status transitions
* Workflow rules
* Calculations
* File validation
* Export helpers

## Integration Tests

Test:

* Authentication
* Registration approval
* Role assignment
* Scoped access
* Report submission
* Review workflows
* Approval workflows
* Notifications
* Document versioning
* Exports
* Search
* Audit logging

## Security Tests

Test:

* Unauthorized access
* Horizontal privilege escalation
* Vertical privilege escalation
* Direct object-reference attacks
* Confidential-file access
* Self-approval prevention
* Self-review prevention
* CSRF protection
* XSS protection
* File-upload validation
* Restricted search results
* Export permissions

## Accessibility Tests

Test:

* Keyboard navigation
* Labels
* Heading hierarchy
* Focus management
* Contrast
* Accessible error handling
* Screen-reader support

## Responsive Tests

Test:

* Small mobile
* Large mobile
* Tablet
* Laptop
* Desktop

## Performance Tests

Test:

* Dashboard queries
* Large registers
* Search
* Export generation
* File listings
* Report listings

Use:

* `pytest`
* `pytest-django`
* Django test client
* Coverage reporting
* Factory libraries where appropriate

Maintain meaningful test coverage for critical business logic.

---

# 46. DEVELOPMENT QUALITY TOOLS

Configure:

* Ruff
* Black
* isort
* mypy
* pytest
* pytest-django
* coverage
* Bandit
* djLint
* ESLint
* Prettier
* Stylelint
* pre-commit

Create common development commands for:

* Install
* Run
* Test
* Format
* Lint
* Type check
* Security scan
* Coverage
* Migrations
* Seed data
* Static collection
* Production check

---

# 47. DOCUMENTATION

Create and maintain:

* `README.md`
* `AGENTS.md`
* Development roadmap files
* Installation guide
* Windows setup guide
* Linux setup guide
* macOS setup guide
* Environment-variable guide
* Database guide
* Architecture guide
* User-role guide
* Permission matrix
* Workflow guide
* Report-template guide
* Export guide
* File-storage guide
* Security guide
* Testing guide
* Deployment guide
* Backup and recovery guide
* Administrator manual
* User manual
* API documentation where APIs are introduced
* Change log

Documentation must stay synchronized with implementation.

---

# 48. SEED DATA

Create safe development seed data for:

* SITADC organization
* Organizational units
* Directorates
* Departments
* Positions
* Roles
* Permissions
* Report categories
* Initial report templates
* Statuses
* Workflow definitions
* Confidentiality levels
* Numbering configurations
* Reporting frequencies
* Reporting periods
* Example programs
* Example projects
* Development users

Do not include real beneficiary, safeguarding, whistleblower, financial, or sensitive personal information in seed data.

Clearly mark all seed accounts as development-only.

---

# 49. DEPLOYMENT PREPARATION

Prepare the Django application for secure deployment.

Include:

* Environment-based settings
* Development settings
* Production settings
* Secure secret handling
* Static-file configuration
* Media-file strategy
* Allowed-host configuration
* CSRF trusted origins
* HTTPS configuration
* Secure-cookie settings
* Error logging
* Application logging
* Backup procedures
* Database backup
* Media backup
* Restore procedures
* Health checks
* Deployment checklist
* Django deployment checks

SQLite may be used for initial deployment only where the scale and hosting arrangement remain appropriate.

Clearly document the conditions under which migration to PostgreSQL becomes necessary.

---

# 50. IMPLEMENTATION PHASES

Implement the system phase by phase.

Recommended sequence:

## Phase 0: Governance and Documentation

* AGENTS.md
* README.md
* Master roadmap
* Coding standards
* Naming conventions
* Definition of done

## Phase 1: Project Foundation

* Django project
* Environment configuration
* Base settings
* Shared templates
* Static assets
* Error pages

## Phase 2: Development Tooling

* Formatting
* Linting
* Testing
* Security scanning
* Pre-commit
* CI preparation

## Phase 3: Core Architecture

* Core models
* Shared services
* Base classes
* Utilities
* Soft deletion
* Status management

## Phase 4: Authentication and Accounts

* Login
* Invitation
* Registration
* Approval
* Profiles
* Sessions

## Phase 5: Roles, Permissions and Access Scope

* Roles
* Permissions
* Scope engine
* Permission matrix
* Authorization tests

## Phase 6: Organizational Structure

* Directorates
* Departments
* Regions
* Districts
* Communities
* Teams
* Reporting lines

## Phase 7: Reference Numbering

* Numbering configuration
* Sequence service
* Entity references
* Concurrency tests

## Phase 8: Audit Logging

* Audit model
* Service
* Middleware
* Sensitive-access logs

## Phase 9: UI Design System

* Layout
* Navigation
* Components
* Light mode
* Dark mode
* Responsive behavior
* Accessibility

## Phase 10: Leader Management

## Phase 11: Membership and Volunteer Management

## Phase 12: Stakeholder Management

## Phase 13: Program and Project Management

## Phase 14: Beneficiary Management

## Phase 15: MEAL

## Phase 16: Report Template Builder

## Phase 17: Report Management

## Phase 18: Review and Approval

## Phase 19: Document Management

## Phase 20: Registers

## Phase 21: Meetings and Calendar

## Phase 22: Notifications and Announcements

## Phase 23: Dashboards and Analytics

## Phase 24: Search

## Phase 25: Export Engine

## Phase 26: Governance, Risk, Compliance and Safeguarding

## Phase 27: Finance and Resource Mobilization

## Phase 28: System Configuration

## Phase 29: Security Review

## Phase 30: Accessibility Review

## Phase 31: Performance Review

## Phase 32: Full Testing

## Phase 33: Documentation and Training Materials

## Phase 34: Deployment Preparation

## Phase 35: Final Acceptance and Handover

Do not implement later phases before required dependencies are complete.

---

# 51. AI AGENT WORKING RULES

For every implementation task, the AI agent must:

1. Read `AGENTS.md`.
2. Read the active roadmap.
3. Inspect existing files.
4. Identify dependencies.
5. State the active phase.
6. List the files to create or modify.
7. Preserve existing valid functionality.
8. Use project naming conventions.
9. Implement backend authorization.
10. Add validation.
11. Add audit logging where required.
12. Add tests.
13. Run formatting.
14. Run linting.
15. Run type checks.
16. Run security checks.
17. Run tests.
18. Update documentation.
19. Provide a delivery report.

Do not:

* Generate placeholder-only pages and claim completion.
* Use hard-coded dashboard data.
* Skip permission checks.
* Skip server-side validation.
* duplicate models.
* Introduce a new framework.
* Change the stack without explicit authorization.
* Remove tests to make the build pass.
* suppress errors without resolving their cause.
* expose sensitive records.
* create unrestricted downloads.
* bypass workflow rules.
* mark incomplete work as complete.

---

# 52. REQUIRED DELIVERY REPORT FORMAT

At the end of each development task, provide:

## Task Summary

Describe what was implemented.

## Active Phase

State the roadmap phase.

## Files Created

List new files.

## Files Modified

List changed files.

## Database Changes

List models, fields, constraints, indexes, and migrations.

## Permissions and Security

Explain authorization and privacy controls.

## UI and Accessibility

Explain responsive and accessible behavior.

## Tests Added

List test coverage.

## Commands Run

List:

* Formatting
* Linting
* Type checking
* Security scanning
* Tests
* Django checks

## Results

State what passed and failed.

## Known Limitations

List unresolved issues honestly.

## Next Recommended Task

Identify the next dependency-aware implementation step.

---

# 53. DEFINITION OF DONE

A feature is complete only when:

* Requirements are implemented.
* Models and migrations are valid.
* Permissions are enforced server-side.
* Scope restrictions are enforced.
* Forms include server-side validation.
* Audit logging is implemented where required.
* Templates are responsive.
* Accessibility requirements are addressed.
* Tests are written.
* Tests pass.
* Formatting passes.
* Linting passes.
* Security checks pass.
* Django system checks pass.
* Documentation is updated.
* No critical placeholders remain.
* No unauthorized data is exposed.
* No secrets are hard-coded.
* No duplicate architecture is introduced.
* The feature is connected to related modules.
* The delivery report is completed.

---

# 54. FINAL ACCEPTANCE CRITERIA

The SITADC Youth Hub will be accepted only when:

* Users can register through the approved workflow.
* Administrators can approve and assign accounts.
* Role and scope permissions work correctly.
* Organizational structures are configurable.
* Leaders can be managed.
* Members and volunteers can be managed.
* Stakeholders can be managed.
* Programs and projects can be managed.
* Beneficiaries are securely managed.
* MEAL frameworks and indicators work.
* Reports can be created from configurable templates.
* Reports support drafts and autosave.
* Review and approval workflows work.
* Approved records are locked.
* Documents support secure versioning.
* Registers support filtering and export.
* Dashboards use live authorized data.
* Notifications use real system events.
* Search respects permissions.
* Exports respect permissions and confidentiality.
* Reference numbers are unique and non-reusable.
* Audit histories are complete and protected.
* Sensitive information is restricted.
* The interface works on mobile, tablet, laptop, and desktop.
* Light and dark modes work.
* Keyboard navigation works.
* Critical accessibility checks pass.
* Automated tests pass.
* Security checks pass.
* Documentation is complete.
* Deployment procedures are documented.
* Backup and restoration procedures are tested.
* The application operates as one integrated system.

---

# 55. FINAL COMMAND TO THE AI DEVELOPMENT AGENT

Begin by examining the current project directory.

If the project is empty:

1. Create `AGENTS.md`.
2. Create `README.md`.
3. Create the master development roadmap.
4. Create phase-specific roadmap files.
5. Create the Django project foundation.
6. Configure the required development tools.
7. Implement the system in the approved phase order.

If files already exist:

1. Read them before making changes.
2. Identify the active phase.
3. Preserve correct work.
4. Resolve inconsistencies.
5. Continue from the next incomplete dependency.

Build the SITADC Youth Hub as a secure, integrated, professional organizational management and reporting system using:

* HTML5
* CSS3
* Bootstrap 5
* Vanilla JavaScript
* Python
* Django
* SQLite

Do not replace the required stack.

Do not create disconnected demonstration pages.

Do not claim completion until the defined acceptance criteria and definition of done have been satisfied.

Start with:

**Phase 0 — Project Governance, AGENTS.md, README.md, Master Development Roadmap, Architecture Standards, and Definition of Done.**
