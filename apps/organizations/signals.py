"""
Signals that keep organizational invariants consistent.

The services already enforce the business rules; these signals cover direct
creates through the Django admin so the same rules apply wherever records are
written.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import ActingAppointmentStatus, AppointmentStatus, VacancyStatus
from .models import PositionAssignment, Vacancy


@receiver(post_save, sender=PositionAssignment)
def enforce_single_active_assignment(sender, instance, **kwargs):
    """Ensure a position and person only ever have one active appointment."""
    if instance.status != AppointmentStatus.ACTIVE:
        return
    PositionAssignment.objects.filter(
        position=instance.position,
        status=AppointmentStatus.ACTIVE,
    ).exclude(pk=instance.pk).update(status=AppointmentStatus.ENDED)
    PositionAssignment.objects.filter(
        person=instance.person,
        status=AppointmentStatus.ACTIVE,
    ).exclude(pk=instance.pk).update(status=AppointmentStatus.ENDED)

    vacancy = Vacancy.objects.filter(position=instance.position).first()
    if vacancy and vacancy.recruitment_status != VacancyStatus.FILLED:
        vacancy.recruitment_status = VacancyStatus.FILLED
        vacancy.save(update_fields=["recruitment_status"])

    from .models import ActingAppointment

    ActingAppointment.objects.filter(
        position=instance.position,
        status=ActingAppointmentStatus.ACTIVE,
    ).update(status=ActingAppointmentStatus.ENDED)
