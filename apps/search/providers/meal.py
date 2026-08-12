"""Providers indexing MEAL records."""

from __future__ import annotations

from apps.meal.models import (
    Complaint,
    Evaluation,
    Feedback,
    Indicator,
    LessonLearned,
    MonitoringVisit,
)
from apps.meal.permissions import MEAL_MANAGE, MEAL_VIEW
from apps.meal.selectors import meal_queryset, visible_complaints, visible_feedback

from .base import SearchProvider, register


class _MealRecordProvider(SearchProvider):
    view_permissions = (MEAL_VIEW, MEAL_MANAGE)

    def queryset(self, user):
        return meal_queryset(user, self.model)


class IndicatorProvider(_MealRecordProvider):
    key = "meal.indicator"
    label = "MEAL Indicators"
    model = Indicator
    detail_url_name = "meal:indicator_detail"
    search_fields = (
        "reference_number",
        "code",
        "title",
        "description",
        "formula",
    )
    title_field = "title"
    subtitle_fields = ("code",)
    reference_field = "reference_number"
    status_field = "status"


class MonitoringVisitProvider(_MealRecordProvider):
    key = "meal.monitoring_visit"
    label = "Monitoring Visits"
    model = MonitoringVisit
    detail_url_name = "meal:monitoring_visit_detail"
    search_fields = (
        "reference_number",
        "community",
        "objectives",
        "findings_summary",
        "recommendations",
    )
    title_field = "program__title"
    subtitle_fields = ("community", "visit_date")
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        return meal_queryset(user, self.model).select_related("program")

    def title_value(self, instance):
        title = getattr(instance.program, "title", "") if instance.program_id else ""
        return title or f"Monitoring Visit {instance.reference_number}"


class EvaluationProvider(_MealRecordProvider):
    key = "meal.evaluation"
    label = "Evaluations"
    model = Evaluation
    detail_url_name = "meal:evaluation_detail"
    search_fields = (
        "reference_number",
        "title",
        "findings",
        "conclusions",
        "methodology",
    )[:5]
    title_field = "title"
    subtitle_fields = ("reference_number",)
    reference_field = "reference_number"
    status_field = "status"


class ComplaintProvider(_MealRecordProvider):
    key = "meal.complaint"
    label = "Complaints"
    model = Complaint
    detail_url_name = "meal:complaint_detail"
    search_fields = (
        "reference_number",
        "description",
        "source",
    )
    title_field = "description"
    subtitle_fields = ("source", "submission_date")
    reference_field = "reference_number"
    status_field = "status"

    def title_value(self, instance):
        description = getattr(instance, "description", "") or ""
        if len(description) > 80:
            description = f"{description[:80]}..."
        return description or f"Complaint {instance.reference_number}"

    def queryset(self, user):
        return visible_complaints(user)


class FeedbackProvider(_MealRecordProvider):
    key = "meal.feedback"
    label = "Feedback"
    model = Feedback
    detail_url_name = "meal:feedback_detail"
    search_fields = (
        "reference_number",
        "description",
        "source",
    )
    title_field = "description"
    subtitle_fields = ("source", "submission_date")
    reference_field = "reference_number"
    status_field = "status"

    def title_value(self, instance):
        description = getattr(instance, "description", "") or ""
        if len(description) > 80:
            description = f"{description[:80]}..."
        return description or f"Feedback {instance.reference_number}"

    def queryset(self, user):
        return visible_feedback(user)


class LessonLearnedProvider(_MealRecordProvider):
    key = "meal.lesson"
    label = "Lessons Learned"
    model = LessonLearned
    detail_url_name = "meal:lesson_detail"
    search_fields = (
        "reference_number",
        "title",
        "context",
        "observation",
        "analysis",
        "recommendation",
    )[:6]
    title_field = "title"
    subtitle_fields = ("reference_number",)
    reference_field = "reference_number"
    status_field = "status"


register(IndicatorProvider())
register(MonitoringVisitProvider())
register(EvaluationProvider())
register(ComplaintProvider())
register(FeedbackProvider())
register(LessonLearnedProvider())
