"""
Tests for Configuration models and views.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.configuration.models import (
    ApplicationSettings,
    AuthenticationSettings,
    BackupSchedule,
    BrandingSettings,
    Configuration,
    ConfigurationCategory,
    ConfigurationStatus,
    ConfigurationValue,
    DocumentSettings,
    ExportSettings,
    IntegrationConfiguration,
    MaintenanceWindow,
    NotificationSettings,
    NumberingConfiguration,
    RolePermissionConfiguration,
    SecurityPolicy,
    SystemHealthRecord,
    WorkflowConfiguration,
)
from apps.rbac.models import Role

User = get_user_model()


class ConfigurationModelTests(TestCase):
    """Tests for Configuration models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="Password123!@",
        )

    def test_configuration_creation(self):
        config = Configuration.objects.create(
            category=ConfigurationCategory.APPLICATION,
            key="test_config",
            name="Test Configuration",
            description="Test description",
            status=ConfigurationStatus.DRAFT,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(config.key, "test_config")
        self.assertEqual(config.status, ConfigurationStatus.DRAFT)
        self.assertEqual(config.version, 1)

    def test_configuration_status_transition(self):
        config = Configuration.objects.create(
            category=ConfigurationCategory.APPLICATION,
            key="test_transition",
            name="Test Transition",
            status=ConfigurationStatus.DRAFT,
            created_by=self.user,
            updated_by=self.user,
        )

        # Valid transitions
        self.assertTrue(config.can_transition_to(ConfigurationStatus.VALIDATION))
        config.transition_to(ConfigurationStatus.VALIDATION, self.user)
        self.assertEqual(config.status, ConfigurationStatus.VALIDATION)

        self.assertTrue(config.can_transition_to(ConfigurationStatus.REVIEW))
        config.transition_to(ConfigurationStatus.REVIEW, self.user)
        self.assertEqual(config.status, ConfigurationStatus.REVIEW)

        self.assertTrue(config.can_transition_to(ConfigurationStatus.APPROVAL))
        config.transition_to(ConfigurationStatus.APPROVAL, self.user)
        self.assertEqual(config.status, ConfigurationStatus.APPROVAL)

        self.assertTrue(config.can_transition_to(ConfigurationStatus.ACTIVE))
        config.transition_to(ConfigurationStatus.ACTIVE, self.user)
        self.assertEqual(config.status, ConfigurationStatus.ACTIVE)

        # Invalid transition
        self.assertFalse(config.can_transition_to(ConfigurationStatus.DRAFT))

    def test_configuration_version_creation(self):
        config = Configuration.objects.create(
            category=ConfigurationCategory.APPLICATION,
            key="version_test",
            name="Version Test",
            created_by=self.user,
            updated_by=self.user,
        )

        ConfigurationValue.objects.create(
            configuration=config,
            key="setting1",
            value="value1",
            created_by=self.user,
            updated_by=self.user,
        )

        # Version should be incremented
        config.refresh_from_db()
        self.assertEqual(config.version, 2)

        versions = config.versions.all()
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().version, 2)

    def test_configuration_timeline_logging(self):
        config = Configuration.objects.create(
            category=ConfigurationCategory.APPLICATION,
            key="timeline_test",
            name="Timeline Test",
            status=ConfigurationStatus.DRAFT,
            created_by=self.user,
            updated_by=self.user,
        )

        timeline = config.timeline.all()
        self.assertEqual(timeline.count(), 1)
        self.assertEqual(timeline.first().event_type, "created")


class SingletonSettingsTests(TestCase):
    """Tests for singleton settings models."""

    def test_application_settings_singleton(self):
        settings1 = ApplicationSettings.load()
        settings2 = ApplicationSettings.load()
        self.assertEqual(settings1.pk, settings2.pk)

    def test_authentication_settings_singleton(self):
        settings1 = AuthenticationSettings.load()
        settings2 = AuthenticationSettings.load()
        self.assertEqual(settings1.pk, settings2.pk)

    def test_notification_settings_singleton(self):
        settings1 = NotificationSettings.load()
        settings2 = NotificationSettings.load()
        self.assertEqual(settings1.pk, settings2.pk)

    def test_branding_settings_singleton(self):
        settings1 = BrandingSettings.load()
        settings2 = BrandingSettings.load()
        self.assertEqual(settings1.pk, settings2.pk)

    def test_document_settings_singleton(self):
        settings1 = DocumentSettings.load()
        settings2 = DocumentSettings.load()
        self.assertEqual(settings1.pk, settings2.pk)

    def test_export_settings_singleton(self):
        settings1 = ExportSettings.load()
        settings2 = ExportSettings.load()
        self.assertEqual(settings1.pk, settings2.pk)


class NumberingConfigurationTests(TestCase):
    """Tests for NumberingConfiguration."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test6@example.com",
            username="testuser6",
            password="Password123!@",
        )

    def test_numbering_configuration(self):
        config = NumberingConfiguration.objects.create(
            module="reports",
            prefix="RPT",
            format="{year}-{sequence:04d}",
            sequence=1,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(config.module, "reports")
        self.assertEqual(config.prefix, "RPT")
        self.assertEqual(config.sequence, 1)


class SecurityPolicyTests(TestCase):
    """Tests for SecurityPolicy."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test7@example.com",
            username="testuser7",
            password="Password123!@",
        )

    def test_security_policy_creation(self):
        policy = SecurityPolicy.objects.create(
            name="Password Policy",
            slug="password-policy",
            policy_type="password",
            rules={"min_length": 12, "require_special": True},
            enforcement_level="enforce",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(policy.policy_type, "password")
        self.assertEqual(policy.enforcement_level, "enforce")


class BackupScheduleTests(TestCase):
    """Tests for BackupSchedule."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test8@example.com",
            username="testuser8",
            password="Password123!@",
        )

    def test_backup_schedule_creation(self):
        schedule = BackupSchedule.objects.create(
            name="Daily Database Backup",
            backup_type="database",
            frequency="daily",
            schedule_time="02:00",
            retention_days=30,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(schedule.backup_type, "database")
        self.assertEqual(schedule.frequency, "daily")


class IntegrationConfigurationTests(TestCase):
    """Tests for IntegrationConfiguration."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test9@example.com",
            username="testuser9",
            password="Password123!@",
        )

    def test_integration_configuration_creation(self):
        integration = IntegrationConfiguration.objects.create(
            name="Email Service",
            slug="email-service",
            integration_type="email",
            provider="SendGrid",
            base_url="https://api.sendgrid.com",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(integration.integration_type, "email")
        self.assertEqual(integration.provider, "SendGrid")


class MaintenanceWindowTests(TestCase):
    """Tests for MaintenanceWindow."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test10@example.com",
            username="testuser10",
            password="Password123!@",
        )

    def test_maintenance_window_creation(self):
        window = MaintenanceWindow.objects.create(
            name="Weekly Maintenance",
            maintenance_type="scheduled",
            start_time=timezone.now() + timezone.timedelta(days=7),
            end_time=timezone.now() + timezone.timedelta(days=7, hours=2),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(window.maintenance_type, "scheduled")
        self.assertEqual(window.status, "planned")


class WorkflowConfigurationTests(TestCase):
    """Tests for WorkflowConfiguration."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test11@example.com",
            username="testuser11",
            password="Password123!@",
        )

    def test_workflow_configuration_creation(self):
        workflow = WorkflowConfiguration.objects.create(
            name="Report Approval",
            slug="report-approval",
            module="reports",
            entity_type="ReportInstance",
            stages=[{"name": "draft"}, {"name": "review"}, {"name": "approved"}],
            transitions=[
                {"from": "draft", "to": "review"},
                {"from": "review", "to": "approved"},
            ],
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(workflow.module, "reports")
        self.assertEqual(len(workflow.stages), 3)


class RolePermissionConfigurationTests(TestCase):
    """Tests for RolePermissionConfiguration."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test12@example.com",
            username="testuser12",
            password="Password123!@",
        )
        self.role = Role.objects.create(
            name="Test Role",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_role_permission_configuration(self):
        perm = RolePermissionConfiguration.objects.create(
            role=self.role,
            module="reports",
            permissions=["view", "create", "update"],
            scope="organization",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(perm.role, self.role)
        self.assertEqual(perm.module, "reports")
        self.assertEqual(perm.scope, "organization")


class SystemHealthRecordTests(TestCase):
    """Tests for SystemHealthRecord."""

    def test_system_health_record_creation(self):
        record = SystemHealthRecord.objects.create(
            component="database",
            metric_name="connection_pool_usage",
            value=75.5,
            unit="%",
            status="warning",
            threshold_warning=70,
            threshold_critical=90,
        )
        self.assertEqual(record.component, "database")
        self.assertEqual(record.status, "warning")


class ConfigurationAPITests(TestCase):
    """Tests for Configuration API endpoints."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="apiuser@example.com",
            username="apiuser",
            password="Password123!@",
        )
        self.client.force_login(self.user)

        self.config = Configuration.objects.create(
            category=ConfigurationCategory.APPLICATION,
            key="api_test",
            name="API Test",
            status=ConfigurationStatus.DRAFT,
            created_by=self.user,
            updated_by=self.user,
        )

    def test_configuration_status_transition_api(self):
        response = self.client.post(
            f"/configuration/configurations/{self.config.pk}/transition/",
            {"status": ConfigurationStatus.VALIDATION},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.config.refresh_from_db()
        self.assertEqual(self.config.status, ConfigurationStatus.VALIDATION)

    def test_health_check_api(self):
        response = self.client.post("/configuration/health/check/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
