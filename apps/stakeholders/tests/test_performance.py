"""Directory pagination and bounded-query regression tests."""

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.stakeholders.constants import ConfidentialityLevel

from .base import StakeholderTestCase


class StakeholderDirectoryPerformanceTests(StakeholderTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(self.viewer, "partners.view_directory")
        self.client.force_login(self.viewer)
        category = self.taxonomy("CATEGORY", "partner")
        sector = self.taxonomy("SECTOR", "education")
        for index in range(30):
            stakeholder = self.create_stakeholder(
                legal_name=f"Directory Partner {index:02d}",
                confidentiality=ConfidentialityLevel.DIRECTORY,
            )
            stakeholder.categories.add(category)
            stakeholder.sectors.add(sector)

    def test_directory_is_paginated_at_twenty_four_records(self):
        response = self.client.get(reverse("stakeholders:directory"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paginator"].per_page, 24)
        self.assertEqual(len(response.context["stakeholders"]), 24)
        second_page = self.client.get(reverse("stakeholders:directory"), {"page": 2})
        self.assertEqual(len(second_page.context["stakeholders"]), 6)

    def test_directory_query_count_is_bounded_with_prefetched_taxonomies(self):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(reverse("stakeholders:directory"))
            list(response.context["stakeholders"])
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(captured), 20, captured.captured_queries)
