"""
Seed data for the reference numbering module.

This module is the single source of truth for the default reference number
schemes installed by the ``seed_reference_schemes`` management command.  The
prefix catalogue follows the reference numbering specification.
"""

from __future__ import annotations

from .constants import ReferenceModules, SequenceResetPeriod

DEFAULT_PATTERN = "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}"
DEFAULT_ORG = "SITADC"
DEFAULT_SEQUENCE_LENGTH = 6


class SchemeSeed:
    """Plain-data description of a default reference number scheme."""

    def __init__(
        self,
        code: str,
        name: str,
        module: str,
        record_type: str,
        prefix: str,
        description: str,
        organization_code: str = DEFAULT_ORG,
        pattern: str = DEFAULT_PATTERN,
        sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
        reset_period: str = SequenceResetPeriod.NEVER,
        is_default_for_module: bool = True,
        is_default_for_record_type: bool = True,
        is_fallback: bool = False,
    ) -> None:
        self.code = code
        self.name = name
        self.module = module
        self.record_type = record_type
        self.prefix = prefix
        self.description = description
        self.organization_code = organization_code
        self.pattern = pattern
        self.sequence_length = sequence_length
        self.reset_period = reset_period
        self.is_default_for_module = is_default_for_module
        self.is_default_for_record_type = is_default_for_record_type
        self.is_fallback = is_fallback


DEFAULT_SCHEMES: tuple[SchemeSeed, ...] = (
    SchemeSeed(
        code="account",
        name="Account",
        module=ReferenceModules.USERS,
        record_type="account",
        prefix="USR",
        description="Accounts and user profiles.",
    ),
    SchemeSeed(
        code="member",
        name="Member",
        module=ReferenceModules.MEMBERSHIPS,
        record_type="member",
        prefix="MEM",
        description="Membership records.",
    ),
    SchemeSeed(
        code="membership_application",
        name="Membership Application",
        module=ReferenceModules.MEMBERSHIPS,
        record_type="application",
        prefix="APL",
        description="Membership applications.",
        is_default_for_module=False,
    ),
    SchemeSeed(
        code="membership_receipt",
        name="Membership Receipt",
        module=ReferenceModules.MEMBERSHIPS,
        record_type="receipt",
        prefix="RCT",
        description="Membership payment receipts.",
        is_default_for_module=False,
    ),
    SchemeSeed(
        code="membership_card",
        name="Membership Card",
        module=ReferenceModules.MEMBERSHIPS,
        record_type="card",
        prefix="CRD",
        description="Membership cards.",
        is_default_for_module=False,
    ),
    SchemeSeed(
        code="volunteer",
        name="Volunteer",
        module=ReferenceModules.VOLUNTEERS,
        record_type="volunteer",
        prefix="VOL",
        description="Volunteer records.",
    ),
    SchemeSeed(
        code="volunteer_application",
        name="Volunteer Application",
        module=ReferenceModules.VOLUNTEERS,
        record_type="application",
        prefix="VAP",
        description="Volunteer recruitment applications.",
        is_default_for_module=False,
    ),
    SchemeSeed(
        code="volunteer_recruitment",
        name="Volunteer Recruitment Campaign",
        module=ReferenceModules.VOLUNTEERS,
        record_type="recruitment",
        prefix="VRC",
        description="Volunteer recruitment campaigns.",
        is_default_for_module=False,
    ),
    SchemeSeed(
        code="volunteer_disciplinary",
        name="Volunteer Disciplinary Record",
        module=ReferenceModules.VOLUNTEERS,
        record_type="disciplinary",
        prefix="VDC",
        description="Volunteer disciplinary records.",
        is_default_for_module=False,
    ),
    SchemeSeed(
        code="leader",
        name="Leader",
        module=ReferenceModules.LEADERS,
        record_type="leader",
        prefix="LDR",
        description="Leadership positions and holders.",
    ),
    SchemeSeed(
        code="report",
        name="Report",
        module=ReferenceModules.REPORTS,
        record_type="report",
        prefix="RPT",
        description="Reports.",
    ),
    SchemeSeed(
        code="document",
        name="Document",
        module=ReferenceModules.DOCUMENTS,
        record_type="document",
        prefix="DOC",
        description="Documents and file records.",
    ),
    SchemeSeed(
        code="program",
        name="Program",
        module=ReferenceModules.PROGRAMS,
        record_type="program",
        prefix="PRG",
        description="Programs.",
    ),
    SchemeSeed(
        code="project",
        name="Project",
        module=ReferenceModules.PROJECTS,
        record_type="project",
        prefix="PRJ",
        description="Projects.",
    ),
    SchemeSeed(
        code="event",
        name="Event",
        module=ReferenceModules.EVENTS,
        record_type="event",
        prefix="EVT",
        description="Events.",
    ),
    SchemeSeed(
        code="asset",
        name="Asset",
        module=ReferenceModules.FINANCE,
        record_type="asset",
        prefix="AST",
        description="Assets.",
    ),
    SchemeSeed(
        code="finance",
        name="Finance",
        module=ReferenceModules.FINANCE,
        record_type="transaction",
        prefix="FIN",
        description="Financial transactions.",
    ),
    SchemeSeed(
        code="meeting",
        name="Meeting",
        module=ReferenceModules.MEETINGS,
        record_type="meeting",
        prefix="MTG",
        description="Meetings.",
    ),
    SchemeSeed(
        code="grant",
        name="Grant",
        module=ReferenceModules.GRANTS,
        record_type="grant",
        prefix="GRT",
        description="Grants.",
    ),
    SchemeSeed(
        code="partner",
        name="Partner",
        module=ReferenceModules.PARTNERS,
        record_type="partner",
        prefix="PAR",
        description="Partners.",
    ),
    SchemeSeed(
        code="donor",
        name="Donor",
        module=ReferenceModules.DONORS,
        record_type="donor",
        prefix="DON",
        description="Donors and sponsors.",
    ),
    SchemeSeed(
        code="beneficiary",
        name="Beneficiary",
        module=ReferenceModules.BENEFICIARIES,
        record_type="beneficiary",
        prefix="BEN",
        description="Beneficiaries.",
    ),
    SchemeSeed(
        code="theory_of_change",
        name="Theory of Change",
        module=ReferenceModules.MEAL,
        record_type="theory_of_change",
        prefix="TOC",
        description="Theories of change.",
    ),
    SchemeSeed(
        code="results_framework",
        name="Results Framework",
        module=ReferenceModules.MEAL,
        record_type="results_framework",
        prefix="RFR",
        description="Results frameworks.",
    ),
    SchemeSeed(
        code="logframe",
        name="Logical Framework",
        module=ReferenceModules.MEAL,
        record_type="logframe",
        prefix="LGF",
        description="Logical frameworks.",
    ),
    SchemeSeed(
        code="indicator",
        name="Indicator",
        module=ReferenceModules.MEAL,
        record_type="indicator",
        prefix="IND",
        description="Indicators in the registry.",
    ),
    SchemeSeed(
        code="indicator_baseline",
        name="Indicator Baseline",
        module=ReferenceModules.MEAL,
        record_type="baseline",
        prefix="BSL",
        description="Indicator baselines.",
    ),
    SchemeSeed(
        code="indicator_target",
        name="Indicator Target",
        module=ReferenceModules.MEAL,
        record_type="target",
        prefix="TGT",
        description="Indicator targets.",
    ),
    SchemeSeed(
        code="data_collection_plan",
        name="Data Collection Plan",
        module=ReferenceModules.MEAL,
        record_type="data_collection_plan",
        prefix="DCP",
        description="Data collection plans.",
    ),
    SchemeSeed(
        code="monitoring_plan",
        name="Monitoring Plan",
        module=ReferenceModules.MEAL,
        record_type="monitoring_plan",
        prefix="MNP",
        description="Monitoring plans.",
    ),
    SchemeSeed(
        code="monitoring_visit",
        name="Monitoring Visit",
        module=ReferenceModules.MEAL,
        record_type="monitoring_visit",
        prefix="MON",
        description="Monitoring visits.",
    ),
    SchemeSeed(
        code="evaluation",
        name="Evaluation",
        module=ReferenceModules.MEAL,
        record_type="evaluation",
        prefix="EVL",
        description="Evaluations.",
    ),
    SchemeSeed(
        code="dqa",
        name="Data Quality Assessment",
        module=ReferenceModules.MEAL,
        record_type="dqa",
        prefix="DQA",
        description="Data quality assessments.",
    ),
    SchemeSeed(
        code="complaint",
        name="Complaint",
        module=ReferenceModules.MEAL,
        record_type="complaint",
        prefix="CMP",
        description="Complaints.",
    ),
    SchemeSeed(
        code="feedback",
        name="Feedback",
        module=ReferenceModules.MEAL,
        record_type="feedback",
        prefix="FDB",
        description="Feedback records.",
    ),
    SchemeSeed(
        code="corrective_action",
        name="Corrective Action",
        module=ReferenceModules.MEAL,
        record_type="corrective_action",
        prefix="CRA",
        description="Corrective actions.",
    ),
    SchemeSeed(
        code="outcome_harvest",
        name="Outcome Harvest",
        module=ReferenceModules.MEAL,
        record_type="outcome_harvest",
        prefix="OCH",
        description="Harvested outcomes.",
    ),
    SchemeSeed(
        code="learning_log",
        name="Learning Log",
        module=ReferenceModules.MEAL,
        record_type="learning_log",
        prefix="LLG",
        description="Learning log entries.",
    ),
    SchemeSeed(
        code="best_practice",
        name="Best Practice",
        module=ReferenceModules.MEAL,
        record_type="best_practice",
        prefix="BPR",
        description="Best practices.",
    ),
    SchemeSeed(
        code="meal_lesson",
        name="Lesson Learned",
        module=ReferenceModules.MEAL,
        record_type="lesson",
        prefix="LSN",
        description="Lessons learned.",
    ),
    SchemeSeed(
        code="scorecard",
        name="Performance Scorecard",
        module=ReferenceModules.MEAL,
        record_type="scorecard",
        prefix="SCR",
        description="Performance scorecards.",
    ),
    SchemeSeed(
        code="meal_report",
        name="MEAL Report",
        module=ReferenceModules.MEAL,
        record_type="meal_report",
        prefix="MRL",
        description="MEAL reports.",
    ),
    SchemeSeed(
        code="organizational_kpi",
        name="Organizational KPI",
        module=ReferenceModules.MEAL,
        record_type="organizational_kpi",
        prefix="KPI",
        description="Organizational KPIs.",
        is_default_for_module=False,
    ),
    SchemeSeed(
        code="register_entry",
        name="Register Entry",
        module=ReferenceModules.REGISTERS,
        record_type="entry",
        prefix="REG",
        description="Organizational register entries.",
    ),
)
