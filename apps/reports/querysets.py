"""QuerySets for Dynamic Report Builder records."""

from __future__ import annotations

from django.db import models
from django.db.models import Count, Q


class ReportTemplateQuerySet(models.QuerySet):
    """QuerySet helpers for report template directory reads."""

    def published(self):
        return self.filter(status="PUBLISHED")

    def drafts(self):
        return self.filter(status="DRAFT")

    def archived(self):
        return self.filter(status="ARCHIVED")

    def by_category(self, category_code: str):
        return self.filter(category__code=category_code)

    def with_category(self):
        return self.select_related("category", "owner", "current_version")

    def search(self, term: str):
        return self.filter(
            Q(title__icontains=term)
            | Q(code__icontains=term)
            | Q(reference_number__icontains=term)
            | Q(description__icontains=term)
            | Q(department__icontains=term)
        )

    def with_counts(self):
        return self.annotate(
            section_count=Count("sections", distinct=True),
            version_count=Count("versions", distinct=True),
        )


class ReportCategoryQuerySet(models.QuerySet):
    """QuerySet helpers for report categories."""

    def active(self):
        return self.filter(is_active=True)

    def with_template_counts(self):
        return self.annotate(
            template_count=Count("templates", distinct=True),
            published_count=Count(
                "templates", filter=Q(templates__status="PUBLISHED"), distinct=True
            ),
        )
