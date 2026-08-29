"""Tests for the dashboard home view and widget services."""

import pytest
from django.urls import reverse

from apps.accounts.constants import AccountStatus
from apps.dashboard.models import DashboardWidgetConfiguration
from apps.dashboard.services import (
    get_default_configuration,
    get_stat_cards,
    resolve_widget_payload,
)

pytestmark = pytest.mark.django_db


def _active_user(django_user_model, **overrides):
    params = {
        "email": "member@example.com",
        "username": "member",
        "first_name": "Plain",
        "last_name": "Member",
        "password": "Password123!@",
    }
    params.update(overrides)
    user = django_user_model.objects.create_user(**params)
    user.status = AccountStatus.ACTIVE
    user.save()
    return user


class TestDashboardHomeView:
    def test_requires_login(self, client):
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 302
        assert reverse("core:login") in response.url

    def test_renders_for_active_user(self, client, django_user_model):
        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
        # Time-of-day greeting plus the user's first name.
        assert "Plain" in response.context["welcome"]["display_name"]
        assert response.context["welcome"]["greeting"] in (
            "Good morning",
            "Good afternoon",
            "Good evening",
        )
        assert "Key performance indicators" in response.content.decode()

    def test_superuser_sees_all_stat_sections(self, client, django_user_model):
        user = django_user_model.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            first_name="Site",
            last_name="Admin",
            password="Password123!@",
        )
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        stat_keys = {card["key"] for card in response.context["stat_cards"]}
        expected = {
            "active_members",
            "active_volunteers",
            "active_programs",
            "active_projects",
            "beneficiaries",
            "stakeholders",
            "overdue_reports",
            "documents",
        }
        assert expected.issubset(stat_keys)

        main_types = {w["widget_type"] for w in response.context["main_widgets"]}
        assert {"quick_actions", "notification", "activity"}.issubset(main_types)

    def test_restricted_user_hides_gated_statistics(self, client, django_user_model):
        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))

        stat_keys = {card["key"] for card in response.context["stat_cards"]}
        # Unrestricted cards stay visible...
        assert "active_members" in stat_keys
        # ...permission-gated cards are hidden.
        assert "beneficiaries" not in stat_keys
        assert "stakeholders" not in stat_keys
        assert "reports_pending_review" not in stat_keys

        quick_urls = {
            action["url_name"]
            for widget in response.context["main_widgets"]
            if widget["widget_type"] == "quick_actions"
            for action in widget["payload"]["actions"]
        }
        assert "beneficiaries:create" not in quick_urls
        assert "stakeholders:create" not in quick_urls


class TestWidgetEndpoints:
    def test_widget_config_returns_seeded_stats(self, client, django_user_model):
        user = django_user_model.objects.create_superuser(
            email="admin2@example.com",
            username="admin2",
            first_name="Site",
            last_name="Admin",
            password="Password123!@",
        )
        client.force_login(user)
        response = client.get(reverse("dashboard:widget_config", args=["stats"]))
        assert response.status_code == 200

        widgets = response.json()["widgets"]
        stat_keys = {w["configuration"].get("stat_key") for w in widgets}
        assert "active_members" in stat_keys
        assert len(widgets) >= 10

    def test_widget_data_returns_payload(self, client, django_user_model):
        user = django_user_model.objects.create_superuser(
            email="admin3@example.com",
            username="admin3",
            first_name="Site",
            last_name="Admin",
            password="Password123!@",
        )
        client.force_login(user)

        config = get_default_configuration()
        activity_config = DashboardWidgetConfiguration.objects.filter(
            dashboard_configuration=config,
            widget__widget_type="activity",
            is_visible=True,
        ).first()
        assert activity_config is not None

        response = client.get(
            reverse("dashboard:widget_data", args=[activity_config.id])
        )
        assert response.status_code == 200
        assert "entries" in response.json()

    def test_widget_data_unknown_id_returns_404(self, client, django_user_model):
        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:widget_data", args=[999999]))
        assert response.status_code == 404


class TestServices:
    def test_get_stat_cards_respects_permissions(self, django_user_model):
        superuser = django_user_model.objects.create_superuser(
            email="svc-admin@example.com",
            username="svc-admin",
            password="Password123!@",
        )
        restricted = _active_user(django_user_model)

        admin_keys = {card["key"] for card in get_stat_cards(superuser)}
        member_keys = {card["key"] for card in get_stat_cards(restricted)}

        assert "beneficiaries" in admin_keys
        assert "beneficiaries" not in member_keys
        assert "active_members" in member_keys

    def test_resolve_widget_payload_handles_unknown_stat(self, django_user_model):
        from apps.dashboard.models import DashboardWidget

        user = _active_user(django_user_model)
        config = get_default_configuration()
        widget = DashboardWidget.objects.create(
            name="Unknown Statistic",
            widget_type="statistic",
            title="Mystery Metric",
            configuration={"stat_key": "does_not_exist"},
        )
        widget_config = DashboardWidgetConfiguration.objects.create(
            dashboard_configuration=config,
            widget=widget,
            position=99,
        )

        payload = resolve_widget_payload(widget_config, user)
        assert payload["value"] == "--"


class TestPersonalization:
    def _first_visible_widget(self, user):
        config = get_default_configuration()
        configs = (
            DashboardWidgetConfiguration.objects.filter(
                dashboard_configuration=config,
                is_visible=True,
                widget__is_enabled=True,
            )
            .exclude(
                widget__widget_type__in=[
                    "welcome",
                    "profile",
                    "organizational_info",
                    "statistic",
                ]
            )
            .order_by("position")
        )
        return list(configs)

    def test_hidden_widget_not_rendered(self, client, django_user_model):
        from apps.dashboard.models import UserWidgetState

        user = _active_user(django_user_model)
        client.force_login(user)

        configs = self._first_visible_widget(user)
        target = configs[0]
        UserWidgetState.objects.create(
            user=user, widget_id=target.widget_id, is_hidden=True
        )

        response = client.get(reverse("dashboard:home"))
        rendered_ids = {w["id"] for w in response.context["main_widgets"]}
        assert target.id not in rendered_ids
        # Other widgets still render.
        assert rendered_ids

    def test_reposition_overrides_default_order(self, client, django_user_model):
        from apps.dashboard.models import UserWidgetState

        user = _active_user(django_user_model)
        client.force_login(user)

        configs = self._first_visible_widget(user)
        first, second = configs[0], configs[1]
        UserWidgetState.objects.create(
            user=user, widget_id=second.widget_id, position=0
        )

        response = client.get(reverse("dashboard:home"))
        ordered = [
            w["id"]
            for w in response.context["main_widgets"]
            if w["id"] in {first.id, second.id}
        ]
        assert ordered == [second.id, first.id]

    def test_personalize_page_renders(self, client, django_user_model):
        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:personalize"))
        assert response.status_code == 200
        assert b"Widget Layout" in response.content

    def test_save_layout_persists_state(self, client, django_user_model):
        from apps.dashboard.models import UserWidgetState

        user = _active_user(django_user_model)
        client.force_login(user)

        configs = self._first_visible_widget(user)
        hide_target, keep_target = configs[0], configs[1]
        # Unchecked boxes are absent from POST -> widget becomes hidden.
        response = client.post(
            reverse("dashboard:personalize"),
            {
                "action": "layout",
                f"widget_{keep_target.widget_id}_visible": "on",
                f"widget_{keep_target.widget_id}_position": "1",
                f"widget_{hide_target.widget_id}_position": "2",
            },
        )
        assert response.status_code == 302
        hidden_state = UserWidgetState.objects.get(
            user=user, widget_id=hide_target.widget_id
        )
        assert hidden_state.is_hidden is True
        kept_state = UserWidgetState.objects.get(
            user=user, widget_id=keep_target.widget_id
        )
        assert kept_state.is_hidden is False
        assert kept_state.position == 1

    def test_reset_layout_clears_states(self, client, django_user_model):
        from apps.dashboard.models import UserWidgetState

        user = _active_user(django_user_model)
        client.force_login(user)

        target = self._first_visible_widget(user)[0]
        UserWidgetState.objects.create(
            user=user, widget_id=target.widget_id, is_hidden=True
        )
        response = client.post(reverse("dashboard:personalize"), {"action": "reset"})
        assert response.status_code == 302
        assert not UserWidgetState.objects.filter(user=user).exists()

    def test_preferences_saved(self, client, django_user_model):
        from apps.dashboard.models import UserDashboardPreference

        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.post(
            reverse("dashboard:personalize"),
            {
                "action": "preferences",
                "theme": "dark",
                "preferred_chart_style": "bar",
                "default_reporting_period": "this_quarter",
            },
        )
        assert response.status_code == 302
        pref = UserDashboardPreference.objects.get(user=user)
        assert pref.theme == "dark"
        assert pref.preferred_chart_style == "bar"
        assert pref.default_reporting_period == "this_quarter"

    def test_period_filter_persists(self, client, django_user_model):
        from apps.dashboard.models import UserDashboardPreference

        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:home") + "?period=this_quarter")
        assert response.status_code == 200
        pref = UserDashboardPreference.objects.get(user=user)
        assert pref.default_reporting_period == "this_quarter"
        assert response.context["current_period"] == "this_quarter"

    def test_invalid_period_ignored(self, client, django_user_model):
        from apps.dashboard.models import UserDashboardPreference

        user = _active_user(django_user_model)
        client.force_login(user)
        client.get(reverse("dashboard:home") + "?period=hacky_value")
        pref = UserDashboardPreference.objects.get(user=user)
        assert pref.default_reporting_period != "hacky_value"


class TestActivityFeed:
    def test_home_activity_widget_limited_to_five(self, client, django_user_model):
        from apps.dashboard.services import DASHBOARD_ACTIVITY_PREVIEW_LIMIT

        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200

        activity_widgets = [
            w
            for w in response.context["main_widgets"]
            if w["widget_type"] == "activity"
        ]
        assert activity_widgets, "activity widget should render"
        entries = activity_widgets[0]["payload"]["entries"]
        assert len(entries) <= DASHBOARD_ACTIVITY_PREVIEW_LIMIT

    def test_activity_log_requires_login(self, client):
        response = client.get(reverse("dashboard:activity_log"))
        assert response.status_code == 302
        assert reverse("core:login") in response.url

    def test_activity_log_renders_and_paginates(self, client, django_user_model):
        from django.core.paginator import Page

        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:activity_log"))
        assert response.status_code == 200
        assert isinstance(response.context["page_obj"], Page)
        assert "Read more" in client.get(reverse("dashboard:home")).content.decode()


class TestWidgetAdministration:
    def test_configuration_requires_superuser(self, client, django_user_model):
        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:configuration"))
        assert response.status_code == 403

    def test_widget_management_requires_superuser(self, client, django_user_model):
        user = _active_user(django_user_model)
        client.force_login(user)
        response = client.get(reverse("dashboard:widget_management"))
        assert response.status_code == 403

    def test_superuser_sees_management_pages(self, client, django_user_model):
        admin = django_user_model.objects.create_superuser(
            email="wg-admin@example.com",
            username="wg-admin",
            first_name="Widget",
            last_name="Admin",
            password="Password123!@",
        )
        client.force_login(admin)
        assert client.get(reverse("dashboard:configuration")).status_code == 200
        assert client.get(reverse("dashboard:widget_management")).status_code == 200

    def test_toggle_widget_creates_audit_entry(self, client, django_user_model):
        from django.contrib.admin.models import CHANGE, LogEntry

        from apps.dashboard.models import DashboardWidget

        admin = django_user_model.objects.create_superuser(
            email="audit-admin@example.com",
            username="audit-admin",
            first_name="Audit",
            last_name="Admin",
            password="Password123!@",
        )
        client.force_login(admin)
        widget = DashboardWidget.objects.filter(is_enabled=True).first()
        assert widget is not None

        response = client.post(
            reverse("dashboard:widget_management"),
            {"widget_id": widget.id, "enable": "false"},
        )
        assert response.status_code == 302
        widget.refresh_from_db()
        assert widget.is_enabled is False

        entry = LogEntry.objects.filter(object_id=widget.id, action_flag=CHANGE).latest(
            "id"
        )
        assert "disabled" in entry.change_message.lower()
