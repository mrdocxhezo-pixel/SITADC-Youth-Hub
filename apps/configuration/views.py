from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.configuration.forms import (
    ApplicationSettingsForm,
    AuthenticationSettingsForm,
    BackupScheduleForm,
    BrandingSettingsForm,
    ConfigurationForm,
    ConfigurationValueForm,
    DocumentSettingsForm,
    ExportSettingsForm,
    IntegrationConfigurationForm,
    MaintenanceWindowForm,
    NotificationSettingsForm,
    NumberingConfigurationForm,
    OrganizationSettingsForm,
    RolePermissionConfigurationForm,
    SecurityPolicyForm,
    SystemConfigurationDashboardForm,
    WorkflowConfigurationForm,
)
from apps.configuration.models import (
    ApplicationSettings,
    AuthenticationSettings,
    BackupHistory,
    BackupSchedule,
    BrandingSettings,
    Configuration,
    ConfigurationNotification,
    ConfigurationTimeline,
    ConfigurationValue,
    ConfigurationVersion,
    DocumentSettings,
    ExportSettings,
    IntegrationConfiguration,
    MaintenanceWindow,
    NotificationSettings,
    NumberingConfiguration,
    OrganizationSettings,
    RolePermissionConfiguration,
    SecurityPolicy,
    SystemConfigurationDashboard,
    SystemHealthRecord,
    WorkflowConfiguration,
)
from apps.rbac.authorization import user_has_permission


class ConfigurationPermissionMixin(PermissionRequiredMixin):
    """Mixin for configuration permissions."""

    permission_required = "configuration.view"

    def has_permission(self):
        return user_has_permission(self.request.user, self.permission_required)


@method_decorator(login_required, name="dispatch")
class ConfigurationDashboardView(ConfigurationPermissionMixin, TemplateView):
    """System Configuration dashboard."""

    template_name = "configuration/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "total_configurations": Configuration.objects.count(),
                "active_configurations": Configuration.objects.filter(
                    status=Configuration.Status.ACTIVE
                ).count(),
                "draft_configurations": Configuration.objects.filter(
                    status=Configuration.Status.DRAFT
                ).count(),
                "pending_review": Configuration.objects.filter(
                    status=Configuration.Status.REVIEW
                ).count(),
                "pending_approval": Configuration.objects.filter(
                    status=Configuration.Status.APPROVAL
                ).count(),
                "recent_changes": ConfigurationTimeline.objects.select_related(
                    "configuration", "user"
                ).order_by("-created_at")[:10],
                "pending_backups": BackupSchedule.objects.filter(
                    is_active=True
                ).count(),
                "failed_backups": BackupHistory.objects.filter(status="error").count(),
                "integration_errors": IntegrationConfiguration.objects.filter(
                    last_status="error"
                ).count(),
                "health_alerts": SystemHealthRecord.objects.filter(
                    status__in=["warning", "critical"]
                ).count(),
                "maintenance_windows": MaintenanceWindow.objects.filter(
                    start_time__gte=timezone.now(), status__in=["planned", "announced"]
                ).order_by("start_time")[:5],
            }
        )
        return context


# Configuration CRUD Views
@method_decorator(login_required, name="dispatch")
class ConfigurationListView(ConfigurationPermissionMixin, ListView):
    model = Configuration
    template_name = "configuration/configuration_list.html"
    context_object_name = "configurations"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "organization", "reviewed_by", "approved_by", "activated_by"
            )
        )
        category = self.request.GET.get("category")
        status = self.request.GET.get("status")
        search = self.request.GET.get("search")
        if category:
            queryset = queryset.filter(category=category)
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                Q(key__icontains=search)
                | Q(name__icontains=search)
                | Q(description__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Configuration.Category.choices
        context["statuses"] = Configuration.Status.choices
        return context


@method_decorator(login_required, name="dispatch")
class ConfigurationDetailView(ConfigurationPermissionMixin, DetailView):
    model = Configuration
    template_name = "configuration/configuration_detail.html"
    context_object_name = "configuration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["values"] = self.object.values.all()
        context["versions"] = self.object.versions.all()[:10]
        context["timeline"] = self.object.timeline.all()[:20]
        return context


@method_decorator(login_required, name="dispatch")
class ConfigurationCreateView(ConfigurationPermissionMixin, CreateView):
    model = Configuration
    form_class = ConfigurationForm
    template_name = "configuration/configuration_form.html"
    permission_required = "configuration.add"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Configuration created successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


@method_decorator(login_required, name="dispatch")
class ConfigurationUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = Configuration
    form_class = ConfigurationForm
    template_name = "configuration/configuration_form.html"
    permission_required = "configuration.change"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Configuration updated successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


@method_decorator(login_required, name="dispatch")
class ConfigurationDeleteView(ConfigurationPermissionMixin, DeleteView):
    model = Configuration
    template_name = "configuration/configuration_confirm_delete.html"
    permission_required = "configuration.delete"
    success_url = "/configuration/"

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Configuration deleted successfully."))
        return super().delete(request, *args, **kwargs)


# Configuration Value Views
@method_decorator(login_required, name="dispatch")
class ConfigurationValueListView(ConfigurationPermissionMixin, ListView):
    model = ConfigurationValue
    template_name = "configuration/value_list.html"
    context_object_name = "values"
    paginate_by = 50

    def get_queryset(self):
        config_id = self.kwargs.get("configuration_id")
        return ConfigurationValue.objects.filter(
            configuration_id=config_id
        ).select_related("configuration")


@method_decorator(login_required, name="dispatch")
class ConfigurationValueCreateView(ConfigurationPermissionMixin, CreateView):
    model = ConfigurationValue
    form_class = ConfigurationValueForm
    template_name = "configuration/value_form.html"
    permission_required = "configuration.add"

    def get_initial(self):
        initial = super().get_initial()
        initial["configuration"] = get_object_or_404(
            Configuration, pk=self.kwargs["configuration_id"]
        )
        return initial

    def get_success_url(self):
        return self.object.configuration.get_absolute_url()


@method_decorator(login_required, name="dispatch")
class ConfigurationValueUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = ConfigurationValue
    form_class = ConfigurationValueForm
    template_name = "configuration/value_form.html"
    permission_required = "configuration.change"

    def get_success_url(self):
        return self.object.configuration.get_absolute_url()


@method_decorator(login_required, name="dispatch")
class ConfigurationValueDeleteView(ConfigurationPermissionMixin, DeleteView):
    model = ConfigurationValue
    template_name = "configuration/value_confirm_delete.html"
    permission_required = "configuration.delete"

    def get_success_url(self):
        return self.object.configuration.get_absolute_url()


# Settings Singleton Views
class SingletonSettingsViewMixin:
    """Mixin for singleton settings views."""

    def get_object(self):
        return self.model.load()

    def get_success_url(self):
        return self.request.path


@method_decorator(login_required, name="dispatch")
class ApplicationSettingsView(
    SingletonSettingsViewMixin, ConfigurationPermissionMixin, UpdateView
):
    model = ApplicationSettings
    form_class = ApplicationSettingsForm
    template_name = "configuration/settings/application.html"
    permission_required = "configuration.change_applicationsettings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings_section"] = "application"
        return context


@method_decorator(login_required, name="dispatch")
class AuthenticationSettingsView(
    SingletonSettingsViewMixin, ConfigurationPermissionMixin, UpdateView
):
    model = AuthenticationSettings
    form_class = AuthenticationSettingsForm
    template_name = "configuration/settings/authentication.html"
    permission_required = "configuration.change_authenticationsettings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings_section"] = "authentication"
        return context


@method_decorator(login_required, name="dispatch")
class NotificationSettingsView(
    SingletonSettingsViewMixin, ConfigurationPermissionMixin, UpdateView
):
    model = NotificationSettings
    form_class = NotificationSettingsForm
    template_name = "configuration/settings/notifications.html"
    permission_required = "configuration.change_notificationsettings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings_section"] = "notifications"
        return context


@method_decorator(login_required, name="dispatch")
class BrandingSettingsView(
    SingletonSettingsViewMixin, ConfigurationPermissionMixin, UpdateView
):
    model = BrandingSettings
    form_class = BrandingSettingsForm
    template_name = "configuration/settings/branding.html"
    permission_required = "configuration.change_brandingsettings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings_section"] = "branding"
        return context


@method_decorator(login_required, name="dispatch")
class DocumentSettingsView(
    SingletonSettingsViewMixin, ConfigurationPermissionMixin, UpdateView
):
    model = DocumentSettings
    form_class = DocumentSettingsForm
    template_name = "configuration/settings/documents.html"
    permission_required = "configuration.change_documentsettings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings_section"] = "documents"
        return context


@method_decorator(login_required, name="dispatch")
class ExportSettingsView(
    SingletonSettingsViewMixin, ConfigurationPermissionMixin, UpdateView
):
    model = ExportSettings
    form_class = ExportSettingsForm
    template_name = "configuration/settings/exports.html"
    permission_required = "configuration.change_exportsettings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings_section"] = "exports"
        return context


# Organization Settings
@method_decorator(login_required, name="dispatch")
class OrganizationSettingsListView(ConfigurationPermissionMixin, ListView):
    model = OrganizationSettings
    template_name = "configuration/organization_list.html"
    context_object_name = "organizations"
    permission_required = "configuration.view_organizationsettings"


@method_decorator(login_required, name="dispatch")
class OrganizationSettingsDetailView(ConfigurationPermissionMixin, DetailView):
    model = OrganizationSettings
    template_name = "configuration/organization_detail.html"
    context_object_name = "organization"
    permission_required = "configuration.view_organizationsettings"


@method_decorator(login_required, name="dispatch")
class OrganizationSettingsUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = OrganizationSettings
    form_class = OrganizationSettingsForm
    template_name = "configuration/organization_form.html"
    permission_required = "configuration.change_organizationsettings"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Organization settings updated successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


# Numbering Configuration
@method_decorator(login_required, name="dispatch")
class NumberingConfigurationListView(ConfigurationPermissionMixin, ListView):
    model = NumberingConfiguration
    template_name = "configuration/numbering_list.html"
    context_object_name = "numbering_configs"
    permission_required = "configuration.view_numberingconfiguration"


@method_decorator(login_required, name="dispatch")
class NumberingConfigurationCreateView(ConfigurationPermissionMixin, CreateView):
    model = NumberingConfiguration
    form_class = NumberingConfigurationForm
    template_name = "configuration/numbering_form.html"
    permission_required = "configuration.add_numberingconfiguration"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Numbering configuration created successfully.")
        )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class NumberingConfigurationUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = NumberingConfiguration
    form_class = NumberingConfigurationForm
    template_name = "configuration/numbering_form.html"
    permission_required = "configuration.change_numberingconfiguration"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Numbering configuration updated successfully.")
        )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class NumberingConfigurationDeleteView(ConfigurationPermissionMixin, DeleteView):
    model = NumberingConfiguration
    template_name = "configuration/numbering_confirm_delete.html"
    permission_required = "configuration.delete_numberingconfiguration"
    success_url = "/configuration/numbering/"


# Security Policies
@method_decorator(login_required, name="dispatch")
class SecurityPolicyListView(ConfigurationPermissionMixin, ListView):
    model = SecurityPolicy
    template_name = "configuration/security_policy_list.html"
    context_object_name = "policies"
    permission_required = "configuration.view_securitypolicy"


@method_decorator(login_required, name="dispatch")
class SecurityPolicyDetailView(ConfigurationPermissionMixin, DetailView):
    model = SecurityPolicy
    template_name = "configuration/security_policy_detail.html"
    context_object_name = "policy"
    permission_required = "configuration.view_securitypolicy"


@method_decorator(login_required, name="dispatch")
class SecurityPolicyCreateView(ConfigurationPermissionMixin, CreateView):
    model = SecurityPolicy
    form_class = SecurityPolicyForm
    template_name = "configuration/security_policy_form.html"
    permission_required = "configuration.add_securitypolicy"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Security policy created successfully."))
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class SecurityPolicyUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = SecurityPolicy
    form_class = SecurityPolicyForm
    template_name = "configuration/security_policy_form.html"
    permission_required = "configuration.change_securitypolicy"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Security policy updated successfully."))
        return super().form_valid(form)


# Backup Schedules
@method_decorator(login_required, name="dispatch")
class BackupScheduleListView(ConfigurationPermissionMixin, ListView):
    model = BackupSchedule
    template_name = "configuration/backup_list.html"
    context_object_name = "schedules"
    permission_required = "configuration.view_backupschedule"


@method_decorator(login_required, name="dispatch")
class BackupScheduleDetailView(ConfigurationPermissionMixin, DetailView):
    model = BackupSchedule
    template_name = "configuration/backup_detail.html"
    context_object_name = "schedule"
    permission_required = "configuration.view_backupschedule"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["history"] = self.object.history.all()[:20]
        return context


@method_decorator(login_required, name="dispatch")
class BackupScheduleCreateView(ConfigurationPermissionMixin, CreateView):
    model = BackupSchedule
    form_class = BackupScheduleForm
    template_name = "configuration/backup_form.html"
    permission_required = "configuration.add_backupschedule"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Backup schedule created successfully."))
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class BackupScheduleUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = BackupSchedule
    form_class = BackupScheduleForm
    template_name = "configuration/backup_form.html"
    permission_required = "configuration.change_backupschedule"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Backup schedule updated successfully."))
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class BackupScheduleDeleteView(ConfigurationPermissionMixin, DeleteView):
    model = BackupSchedule
    template_name = "configuration/backup_confirm_delete.html"
    permission_required = "configuration.delete_backupschedule"
    success_url = "/configuration/backups/"


# Integration Configurations
@method_decorator(login_required, name="dispatch")
class IntegrationConfigurationListView(ConfigurationPermissionMixin, ListView):
    model = IntegrationConfiguration
    template_name = "configuration/integration_list.html"
    context_object_name = "integrations"
    permission_required = "configuration.view_integrationconfiguration"


@method_decorator(login_required, name="dispatch")
class IntegrationConfigurationDetailView(ConfigurationPermissionMixin, DetailView):
    model = IntegrationConfiguration
    template_name = "configuration/integration_detail.html"
    context_object_name = "integration"
    permission_required = "configuration.view_integrationconfiguration"


@method_decorator(login_required, name="dispatch")
class IntegrationConfigurationCreateView(ConfigurationPermissionMixin, CreateView):
    model = IntegrationConfiguration
    form_class = IntegrationConfigurationForm
    template_name = "configuration/integration_form.html"
    permission_required = "configuration.add_integrationconfiguration"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Integration configuration created successfully.")
        )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class IntegrationConfigurationUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = IntegrationConfiguration
    form_class = IntegrationConfigurationForm
    template_name = "configuration/integration_form.html"
    permission_required = "configuration.change_integrationconfiguration"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Integration configuration updated successfully.")
        )
        return super().form_valid(form)


# Maintenance Windows
@method_decorator(login_required, name="dispatch")
class MaintenanceWindowListView(ConfigurationPermissionMixin, ListView):
    model = MaintenanceWindow
    template_name = "configuration/maintenance_list.html"
    context_object_name = "maintenance_windows"
    permission_required = "configuration.view_maintenancewindow"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("notified_users")


@method_decorator(login_required, name="dispatch")
class MaintenanceWindowDetailView(ConfigurationPermissionMixin, DetailView):
    model = MaintenanceWindow
    template_name = "configuration/maintenance_detail.html"
    context_object_name = "window"
    permission_required = "configuration.view_maintenancewindow"


@method_decorator(login_required, name="dispatch")
class MaintenanceWindowCreateView(ConfigurationPermissionMixin, CreateView):
    model = MaintenanceWindow
    form_class = MaintenanceWindowForm
    template_name = "configuration/maintenance_form.html"
    permission_required = "configuration.add_maintenancewindow"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Maintenance window created successfully."))
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class MaintenanceWindowUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = MaintenanceWindow
    form_class = MaintenanceWindowForm
    template_name = "configuration/maintenance_form.html"
    permission_required = "configuration.change_maintenancewindow"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Maintenance window updated successfully."))
        return super().form_valid(form)


# System Health
@method_decorator(login_required, name="dispatch")
class SystemHealthView(ConfigurationPermissionMixin, ListView):
    model = SystemHealthRecord
    template_name = "configuration/health.html"
    context_object_name = "health_records"
    paginate_by = 50
    permission_required = "configuration.view_systemhealthrecord"

    def get_queryset(self):
        queryset = super().get_queryset()
        component = self.request.GET.get("component")
        status = self.request.GET.get("status")
        if component:
            queryset = queryset.filter(component=component)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["components"] = SystemHealthRecord.COMPONENT_CHOICES
        context["statuses"] = SystemHealthRecord.STATUS_CHOICES
        # Summary stats
        context["health_summary"] = {
            "healthy": SystemHealthRecord.objects.filter(status="healthy").count(),
            "warning": SystemHealthRecord.objects.filter(status="warning").count(),
            "critical": SystemHealthRecord.objects.filter(status="critical").count(),
            "unknown": SystemHealthRecord.objects.filter(status="unknown").count(),
        }
        return context


# Configuration Notifications
@method_decorator(login_required, name="dispatch")
class ConfigurationNotificationListView(LoginRequiredMixin, ListView):
    model = ConfigurationNotification
    template_name = "configuration/notifications.html"
    context_object_name = "notifications"
    paginate_by = 25

    def get_queryset(self):
        return (
            ConfigurationNotification.objects.filter(
                Q(recipients=self.request.user)
                | Q(
                    roles_notified__contains=[
                        str(r.id) for r in self.request.user.roles.all()
                    ]
                )
            )
            .distinct()
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_count"] = self.get_queryset().filter(is_read=False).count()
        return context


@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read."""
    notification = get_object_or_404(ConfigurationNotification, pk=pk)
    if request.user in notification.recipients.all():
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
    return redirect("configuration:notifications")


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    ConfigurationNotification.objects.filter(
        recipients=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())
    return redirect("configuration:notifications")


# AJAX API Views
@login_required
def configuration_status_transition(request, pk):
    """Handle configuration status transitions via AJAX."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed"}, status=405
        )

    configuration = get_object_or_404(Configuration, pk=pk)
    new_status = request.POST.get("status")
    remarks = request.POST.get("remarks", "")

    if not new_status:
        return JsonResponse({"success": False, "error": "Status required"}, status=400)

    try:
        configuration.transition_to(new_status, request.user, remarks)
        return JsonResponse(
            {
                "success": True,
                "message": _("Status changed to %(status)s.")
                % {"status": configuration.get_status_display()},
                "new_status": configuration.status,
            }
        )
    except ValidationError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
def configuration_version_rollback(request, pk):
    """Rollback configuration to a previous version."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed"}, status=405
        )

    configuration = get_object_or_404(Configuration, pk=pk)
    version_id = request.POST.get("version_id")

    if not version_id:
        return JsonResponse(
            {"success": False, "error": "Version ID required"}, status=400
        )

    try:
        version = ConfigurationVersion.objects.get(
            pk=version_id, configuration=configuration
        )
        # Create new version from snapshot
        new_version = ConfigurationVersion.objects.create(
            configuration=configuration,
            version=configuration.version + 1,
            snapshot=version.snapshot,
            change_summary=f"Rollback to version {version.version}",
            changed_by=request.user,
            is_active_version=True,
        )
        # Deactivate other versions
        ConfigurationVersion.objects.filter(configuration=configuration).exclude(
            pk=new_version.pk
        ).update(is_active_version=False)
        # Apply snapshot to configuration values
        ConfigurationValue.objects.filter(configuration=configuration).delete()
        for key, value in version.snapshot.items():
            ConfigurationValue.objects.create(
                configuration=configuration,
                key=key,
                value=value,
                created_by=request.user,
                updated_by=request.user,
            )
        messages.success(
            request,
            _("Configuration rolled back to version %(version)s.")
            % {"version": version.version},
        )
        return JsonResponse(
            {"success": True, "redirect": configuration.get_absolute_url()}
        )
    except ConfigurationVersion.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": _("Version not found")}, status=404
        )


@login_required
def system_health_check(request):
    """Trigger a system health check."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed"}, status=405
        )

    # This would trigger actual health checks in a real implementation
    # For now, return mock data
    return JsonResponse(
        {
            "success": True,
            "message": _("Health check initiated"),
            "checks": [
                {
                    "component": "database",
                    "status": "healthy",
                    "message": "Database connection OK",
                },
                {
                    "component": "storage",
                    "status": "healthy",
                    "message": "Storage accessible",
                },
                {"component": "api", "status": "healthy", "message": "API responding"},
            ],
        }
    )


# Workflow Configuration Views
@method_decorator(login_required, name="dispatch")
class WorkflowConfigurationListView(ConfigurationPermissionMixin, ListView):
    model = WorkflowConfiguration
    template_name = "configuration/workflow_list.html"
    context_object_name = "workflows"
    permission_required = "configuration.view_workflowconfiguration"


@method_decorator(login_required, name="dispatch")
class WorkflowConfigurationDetailView(ConfigurationPermissionMixin, DetailView):
    model = WorkflowConfiguration
    template_name = "configuration/workflow_detail.html"
    context_object_name = "workflow"
    permission_required = "configuration.view_workflowconfiguration"


@method_decorator(login_required, name="dispatch")
class WorkflowConfigurationCreateView(ConfigurationPermissionMixin, CreateView):
    model = WorkflowConfiguration
    form_class = WorkflowConfigurationForm
    template_name = "configuration/workflow_form.html"
    permission_required = "configuration.add_workflowconfiguration"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Workflow configuration created successfully.")
        )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class WorkflowConfigurationUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = WorkflowConfiguration
    form_class = WorkflowConfigurationForm
    template_name = "configuration/workflow_form.html"
    permission_required = "configuration.change_workflowconfiguration"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Workflow configuration updated successfully.")
        )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class WorkflowConfigurationDeleteView(ConfigurationPermissionMixin, DeleteView):
    model = WorkflowConfiguration
    template_name = "configuration/workflow_confirm_delete.html"
    permission_required = "configuration.delete_workflowconfiguration"
    success_url = "/configuration/workflows/"


# Role Permission Configuration Views
@method_decorator(login_required, name="dispatch")
class RolePermissionConfigurationListView(ConfigurationPermissionMixin, ListView):
    model = RolePermissionConfiguration
    template_name = "configuration/role_permission_list.html"
    context_object_name = "permissions"
    permission_required = "configuration.view_rolepermissionconfiguration"

    def get_queryset(self):
        return super().get_queryset().select_related("role")


@method_decorator(login_required, name="dispatch")
class RolePermissionConfigurationCreateView(ConfigurationPermissionMixin, CreateView):
    model = RolePermissionConfiguration
    form_class = RolePermissionConfigurationForm
    template_name = "configuration/role_permission_form.html"
    permission_required = "configuration.add_rolepermissionconfiguration"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Role permission configuration created successfully.")
        )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class RolePermissionConfigurationUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = RolePermissionConfiguration
    form_class = RolePermissionConfigurationForm
    template_name = "configuration/role_permission_form.html"
    permission_required = "configuration.change_rolepermissionconfiguration"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(
            self.request, _("Role permission configuration updated successfully.")
        )
        return super().form_valid(form)


# Dashboard Configuration
@method_decorator(login_required, name="dispatch")
class SystemConfigurationDashboardListView(ConfigurationPermissionMixin, ListView):
    model = SystemConfigurationDashboard
    template_name = "configuration/dashboard_list.html"
    context_object_name = "dashboards"
    permission_required = "configuration.view_systemconfigurationdashboard"


@method_decorator(login_required, name="dispatch")
class SystemConfigurationDashboardCreateView(ConfigurationPermissionMixin, CreateView):
    model = SystemConfigurationDashboard
    form_class = SystemConfigurationDashboardForm
    template_name = "configuration/dashboard_form.html"
    permission_required = "configuration.add_systemconfigurationdashboard"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Dashboard created successfully."))
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class SystemConfigurationDashboardUpdateView(ConfigurationPermissionMixin, UpdateView):
    model = SystemConfigurationDashboard
    form_class = SystemConfigurationDashboardForm
    template_name = "configuration/dashboard_form.html"
    permission_required = "configuration.change_systemconfigurationdashboard"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _("Dashboard updated successfully."))
        return super().form_valid(form)
