from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from apps.qa.models import (
    Defect,
    DefectAssignment,
    DefectResolution,
    QAAuditReference,
    QAConfiguration,
    QANotification,
    QATimeline,
    QualityDashboard,
    QualityMetric,
    RegressionTest,
    ReleaseApproval,
    ReleaseCandidate,
    TestCase,
    TestDataSet,
    TestEnvironment,
    TestEvidence,
    TestExecution,
    TestPlan,
    TestResult,
    TestScenario,
    TestSuite,
    UATSession,
)

QA_MODELS = [
    QAConfiguration,
    TestEnvironment,
    TestDataSet,
    TestPlan,
    TestSuite,
    TestCase,
    TestScenario,
    TestExecution,
    TestResult,
    TestEvidence,
    Defect,
    DefectAssignment,
    DefectResolution,
    RegressionTest,
    UATSession,
    ReleaseCandidate,
    ReleaseApproval,
    QualityMetric,
    QualityDashboard,
    QANotification,
    QATimeline,
    QAAuditReference,
]

QA_PERMISSIONS = {
    "qa": {
        "view_qaconfiguration": "View QA Configuration",
        "manage_qaconfiguration": "Manage QA Configuration",
        "view_testenvironment": "View Test Environment",
        "manage_testenvironment": "Manage Test Environment",
        "view_testdataset": "View Test Data Set",
        "manage_testdataset": "Manage Test Data Set",
        "view_testplan": "View Test Plan",
        "manage_testplan": "Manage Test Plan",
        "view_testsuite": "View Test Suite",
        "manage_testsuite": "Manage Test Suite",
        "view_testcase": "View Test Case",
        "manage_testcase": "Manage Test Case",
        "view_testscenario": "View Test Scenario",
        "manage_testscenario": "Manage Test Scenario",
        "view_testexecution": "View Test Execution",
        "manage_testexecution": "Manage Test Execution",
        "view_testresult": "View Test Result",
        "manage_testresult": "Manage Test Result",
        "view_testevidence": "View Test Evidence",
        "manage_testevidence": "Manage Test Evidence",
        "view_defect": "View Defect",
        "manage_defect": "Manage Defect",
        "view_defectassignment": "View Defect Assignment",
        "manage_defectassignment": "Manage Defect Assignment",
        "view_defectresolution": "View Defect Resolution",
        "manage_defectresolution": "Manage Defect Resolution",
        "view_regressiontest": "View Regression Test",
        "manage_regressiontest": "Manage Regression Test",
        "view_uatsession": "View UAT Session",
        "manage_uatsession": "Manage UAT Session",
        "view_releasecandidate": "View Release Candidate",
        "manage_releasecandidate": "Manage Release Candidate",
        "approve_release": "Approve Release",
        "view_qualitymetric": "View Quality Metric",
        "manage_qualitymetric": "Manage Quality Metric",
        "view_qualitydashboard": "View Quality Dashboard",
        "manage_qualitydashboard": "Manage Quality Dashboard",
        "view_ganotification": "View QA Notification",
        "manage_ganotification": "Manage QA Notification",
        "view_gtimeline": "View QA Timeline",
        "manage_gtimeline": "Manage QA Timeline",
        "view_gauditreference": "View QA Audit Reference",
    }
}


def get_qa_permissions():
    """Get all QA permissions."""
    permissions = []
    for model in QA_MODELS:
        content_type = ContentType.objects.get_for_model(model)
        perms = Permission.objects.filter(content_type=content_type)
        for perm in perms:
            permissions.append(
                {
                    "codename": perm.codename,
                    "name": perm.name,
                    "model": model.__name__,
                }
            )
    return permissions


def seed_qa_permissions(apps, schema_editor):
    """Seed QA permissions for RBAC."""
    from apps.rbac.models import PermissionCategory, RolePermissionGrant

    # Create permission category
    category, _ = PermissionCategory.objects.get_or_create(
        code="qa",
        defaults={
            "name": "Quality Assurance",
            "description": "Quality Assurance and Testing permissions",
            "order": 20,
        },
    )

    # Define role grants
    role_grants = {
        "QA_LEAD": [
            "manage_qaconfiguration",
            "manage_testenvironment",
            "manage_testdataset",
            "manage_testplan",
            "manage_testsuite",
            "manage_testcase",
            "manage_testscenario",
            "manage_testexecution",
            "manage_testresult",
            "manage_testevidence",
            "manage_defect",
            "manage_defectassignment",
            "manage_defectresolution",
            "manage_regressiontest",
            "manage_uatsession",
            "manage_releasecandidate",
            "approve_release",
            "manage_qualitymetric",
            "manage_qualitydashboard",
            "view_ganotification",
            "view_gtimeline",
            "view_gauditreference",
        ],
        "QA_ENGINEER": [
            "view_qaconfiguration",
            "view_testenvironment",
            "view_testdataset",
            "view_testplan",
            "manage_testsuite",
            "manage_testcase",
            "manage_testscenario",
            "manage_testexecution",
            "manage_testresult",
            "manage_testevidence",
            "manage_defect",
            "manage_defectassignment",
            "manage_defectresolution",
            "manage_regressiontest",
            "view_uatsession",
            "view_releasecandidate",
            "view_qualitymetric",
            "view_qualitydashboard",
            "view_ganotification",
            "view_gtimeline",
        ],
        "DEVELOPER": [
            "view_testplan",
            "view_testsuite",
            "view_testcase",
            "view_testscenario",
            "view_testexecution",
            "view_testresult",
            "view_testevidence",
            "view_defect",
            "manage_defectassignment",
            "manage_defectresolution",
            "view_ganotification",
        ],
        "PRODUCT_OWNER": [
            "view_qaconfiguration",
            "view_testplan",
            "view_testsuite",
            "view_testcase",
            "view_testscenario",
            "view_testexecution",
            "view_defect",
            "view_releasecandidate",
            "approve_release",
            "view_qualitymetric",
            "view_qualitydashboard",
            "view_ganotification",
        ],
        "PROJECT_MANAGER": [
            "view_qaconfiguration",
            "view_testenvironment",
            "view_testplan",
            "view_testsuite",
            "view_testcase",
            "view_testscenario",
            "view_testexecution",
            "view_defect",
            "view_releasecandidate",
            "view_qualitymetric",
            "view_qualitydashboard",
            "view_ganotification",
        ],
    }

    for role_code, perm_codenames in role_grants.items():
        from apps.rbac.models import Role

        try:
            role = Role.objects.get(code=role_code)
            for codename in perm_codenames:
                try:
                    perm = Permission.objects.get(codename=codename)
                    RolePermissionGrant.objects.get_or_create(
                        role=role, permission=perm, defaults={"granted_by": None}
                    )
                except Permission.DoesNotExist:
                    pass
        except Role.DoesNotExist:
            pass
