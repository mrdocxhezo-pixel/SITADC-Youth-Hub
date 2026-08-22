from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.configuration.models import (
    ApplicationSettings,
    AuthenticationSettings,
    BrandingSettings,
    Configuration,
    ConfigurationCategory,
    ConfigurationStatus,
    ConfigurationTimeline,
    ConfigurationValue,
    ConfigurationVersion,
    DocumentSettings,
    ExportSettings,
    NotificationSettings,
    SecurityPolicy,
)


def create_configuration_version(sender, instance, created, **kwargs):
    """Create a version snapshot when configuration values change."""
    if isinstance(instance, ConfigurationValue):
        config = instance.configuration
        # Get all current values for this configuration
        values = ConfigurationValue.objects.filter(configuration=config)
        snapshot = {v.key: v.value for v in values}

        # Create new version
        new_version = config.version + 1
        ConfigurationVersion.objects.create(
            configuration=config,
            version=new_version,
            snapshot=snapshot,
            change_summary=f"Value '{instance.key}' updated",
            changed_by=instance.updated_by,
        )
        # Deactivate old versions
        ConfigurationVersion.objects.filter(configuration=config).exclude(
            version=new_version
        ).update(is_active_version=False)
        # Update configuration version
        config.version = new_version
        config.save(update_fields=["version", "updated_at", "updated_by"])


def log_configuration_change(sender, instance, created, **kwargs):
    """Log configuration changes to timeline."""
    if isinstance(instance, Configuration):
        if created:
            ConfigurationTimeline.objects.create(
                configuration=instance,
                event_type="created",
                user=instance.created_by,
                new_value={"status": instance.status, "category": instance.category},
                remarks="Configuration record created",
            )
        else:
            # Track status changes by comparing with database
            try:
                db_instance = Configuration.objects.get(pk=instance.pk)
                if db_instance.status != instance.status:
                    ConfigurationTimeline.objects.create(
                        configuration=instance,
                        event_type=f"status_changed_to_{instance.status}",
                        user=instance.updated_by,
                        previous_value=db_instance.status,
                        new_value=instance.status,
                        remarks=f"Status changed from {db_instance.status} to {instance.status}",
                    )
            except Configuration.DoesNotExist:
                pass


def log_value_change(sender, instance, **kwargs):
    """Log configuration value changes."""
    if isinstance(instance, ConfigurationValue) and not instance._state.adding:
        try:
            db_instance = ConfigurationValue.objects.get(pk=instance.pk)
            if db_instance.value != instance.value:
                ConfigurationTimeline.objects.create(
                    configuration=instance.configuration,
                    event_type="value_changed",
                    user=instance.updated_by,
                    previous_value={"key": instance.key, "value": db_instance.value},
                    new_value={"key": instance.key, "value": instance.value},
                    remarks=f"Value '{instance.key}' updated",
                )
        except ConfigurationValue.DoesNotExist:
            pass


# Connect signals
post_save.connect(create_configuration_version, sender=ConfigurationValue)
post_save.connect(log_configuration_change, sender=Configuration)
pre_save.connect(log_value_change, sender=ConfigurationValue)


# Singleton settings change logging
def log_singleton_change(sender, instance, created, **kwargs):
    """Log changes to singleton settings."""
    if created:
        event_type = "created"
    else:
        event_type = "updated"

    # Find or create a generic configuration record for this singleton
    config, _ = Configuration.objects.get_or_create(
        category=ConfigurationCategory.APPLICATION,
        key=sender.__name__.lower().replace("settings", ""),
        defaults={
            "name": sender._meta.verbose_name,
            "status": ConfigurationStatus.ACTIVE,
            "created_by": instance.created_by,
            "updated_by": instance.updated_by,
        },
    )

    changed_fields = []
    if not created:
        try:
            db_instance = sender.objects.get(pk=instance.pk)
            for field in instance._meta.fields:
                if field.name not in [
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                ]:
                    if getattr(db_instance, field.name) != getattr(
                        instance, field.name
                    ):
                        changed_fields.append(field.name)
        except sender.DoesNotExist:
            pass

    ConfigurationTimeline.objects.create(
        configuration=config,
        event_type=event_type,
        user=instance.updated_by,
        new_value={"updated_fields": changed_fields},
        remarks=f"{sender._meta.verbose_name} {event_type}",
    )


for model in [
    ApplicationSettings,
    AuthenticationSettings,
    NotificationSettings,
    BrandingSettings,
    DocumentSettings,
    ExportSettings,
    SecurityPolicy,
]:
    post_save.connect(log_singleton_change, sender=model)


# Security policy expiry alerts
@receiver(pre_save, sender=SecurityPolicy)
def security_policy_review_alert(sender, instance, **kwargs):
    """Alert when security policy review date is approaching."""
    if (
        instance.review_date
        and instance.review_date <= timezone.now() + timezone.timedelta(days=30)
    ):
        # Create notification for security team
        from apps.configuration.models import ConfigurationNotification
        from apps.rbac.models import Role

        security_roles = Role.objects.filter(
            name__icontains="security"
        ) | Role.objects.filter(name__icontains="admin")
        users = security_roles.values_list("users", flat=True).distinct()

        ConfigurationNotification.objects.create(
            event_type="security_changed",
            configuration=None,
            title=f"Security Policy Review Due: {instance.name}",
            message=f"The security policy '{instance.name}' is due for review on {instance.review_date.strftime('%Y-%m-%d')}.",
            priority="high",
        )
        # Add recipients
        from django.contrib.auth import get_user_model

        User = get_user_model()
        notification = ConfigurationNotification.objects.latest("created_at")
        notification.recipients.set(User.objects.filter(pk__in=users))
