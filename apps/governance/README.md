# Governance, Risk, Compliance and Safeguarding (GRCS) Module

This module implements Phase 29 of the SITADC Youth Hub project: Governance, Risk, Compliance and Safeguarding.

## Overview

The GRCS module provides comprehensive governance, risk management, compliance, and safeguarding capabilities for the SITADC Youth Hub organization. It includes:

- **Governance Management**: Board governance, executive governance, committee management
- **Policy Management**: Centralized policy management with version control and acknowledgements
- **Enterprise Risk Management**: Risk identification, assessment, treatment planning, and monitoring
- **Compliance Management**: Tracking of regulatory, donor, grant, and internal compliance requirements
- **Internal Controls**: Management of financial, operational, administrative, and IT controls
- **Ethics Management**: Ethics investigations and code of conduct enforcement
- **Conflict of Interest Register**: Tracking and management of conflict of interest declarations
- **Safeguarding Management**: Protection of children, vulnerable adults, and whistleblowers
- **Incident Reporting**: Health and safety, security, programme, and operational incidents
- **Complaint Management**: Formal complaint handling and resolution
- **Whistleblower Management**: Confidential reporting of wrongdoing
- **Corrective & Preventive Actions (CAPA)**: Systematic improvement processes
- **Governance Analytics**: Dashboards and reporting for governance oversight

## Models

The module includes the following key models:

1. **GovernanceRecord** - Abstract base model for all governance records
2. **Policy** - Policy management with version control
3. **PolicyVersion** - Version tracking for policies
4. **PolicyAcknowledgement** - Tracking of policy acknowledgements by staff
5. **RiskRegister** - Enterprise risk register
6. **RiskAssessment** - Individual risk assessments
7. **RiskTreatmentPlan** - Risk treatment and mitigation plans
8. **ComplianceRequirement** - Compliance requirements tracking
9. **ComplianceAssessment** - Assessments of compliance with requirements
10. **InternalControl** - Internal controls management
11. **EthicsCase** - Ethics case management
12. **ConflictOfInterestDeclaration** - Conflict of interest declarations
13. **SafeguardingCase** - Safeguarding case management
14. **IncidentReport** - Incident reporting system
15. **Complaint** - Complaint management
16. **WhistleblowerReport** - Confidential whistleblower reporting
17. **CorrectivePreventiveAction** - CAPA management
18. **Document** - Document management for governance records
19. **GovernanceMeeting** - Governance meetings management
20. **MeetingAttendance** - Tracking of meeting attendance
21. **GovernanceNotification** - Governance notifications and alerts
22. **GovernanceTimeline** - Timeline of governance activities

## Features

- Role-based access control (RBAC)
- Confidentiality levels for sensitive information
- Audit trails for all governance activities
- Integration with existing SITADC Youth Hub modules
- Responsive user interface
- Comprehensive reporting and analytics
- Automated notifications and reminders
- Document management and version control
- Meeting management and tracking
- Escalation workflows for high-risk items

## Usage

To use this module, ensure it's included in your `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = [
    ...
    'apps.governance',
    ...
]
```

The module will automatically create the necessary database tables when you run migrations:

```bash
python manage.py makemigrations governance
python manage.py migrate
```

## URL Configuration

The module includes URLs for all major functionalities, accessible under the `/governance/` path:

- `/governance/` - Governance dashboard
- `/governance/policies/` - Policy management
- `/governance/risks/` - Risk register
- `/governance/compliance/` - Compliance management
- `/governance/controls/` - Internal controls
- `/governance/ethics/` - Ethics management
- `/governance/safeguarding/` - Safeguarding management
- `/governance/incidents/` - Incident reporting
- `/governance/complaints/` - Complaint management
- `/governance/whistleblower/` - Whistleblower management
- `/governance/capas/` - Corrective & Preventive Actions
- `/governance/documents/` - Document management
- `/governance/meetings/` - Governance meetings
- `/governance/notifications/` - Governance notifications
- `/governance/timeline/` - Governance timeline

## Dependencies

This module depends on:
- Django 3.2+
- Python 3.8+
- Existing SITADC Youth Hub core apps (accounts, core, rbac, etc.)

## Security Features

- Role-based access control for all governance functions
- Confidentiality levels (Public, Internal, Restricted, Confidential, Highly Confidential)
- Audit logging for all governance activities
- Secure handling of sensitive information (safeguarding cases, whistleblower reports)
- Integration with Django's authentication and authorization systems

## Customization

The module can be customized through:
- Django admin interface for configuration
- Extensible model design for additional fields
- Template overrides for UI customization
- Signal handlers for extending functionality