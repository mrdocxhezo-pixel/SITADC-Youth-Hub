"""
Signals that keep the RBAC permission cache consistent.

The permission cache is stored on the user instance.  Whenever an assignment
or a user's permission set changes, the cache is invalidated so subsequent
authorization checks reflect the latest state.
"""

from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.accounts.models import User

from .authorization import clear_permission_cache
from .models import UserRoleAssignment


@receiver([post_save, post_delete], sender=UserRoleAssignment)
def invalidate_assignment_cache(sender, instance, **kwargs):
    """Invalidate the cached permission codes of the affected user."""
    try:
        user = instance.user
    except User.DoesNotExist:
        return
    clear_permission_cache(user)


@receiver(m2m_changed, sender=User.user_permissions.through)
def invalidate_user_permissions_cache(sender, instance, action, **kwargs):
    """Invalidate the cache when a user's direct permissions change."""
    if action in ("post_add", "post_remove", "post_clear"):
        clear_permission_cache(instance)
