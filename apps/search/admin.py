"""Admin registration for the Enterprise Search module."""

from django.contrib import admin

from .models import RecentSearch, SavedSearch, SearchQueryLog


class ImmutableAdminMixin:
    """Block mutation of append-only records through the admin."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RecentSearch)
class RecentSearchAdmin(admin.ModelAdmin):
    """Recent search history for users."""

    list_display = ("user", "query", "result_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "user__username", "query")
    readonly_fields = (
        "id",
        "user",
        "query",
        "entity_types",
        "result_count",
        "created_at",
    )


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    """Named reusable searches."""

    list_display = ("name", "user", "query", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "query", "user__email")


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(ImmutableAdminMixin, admin.ModelAdmin):
    """Immutable audit trail of executed search queries."""

    list_display = ("user", "query", "result_count", "duration_ms", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "user__username", "query")
    readonly_fields = (
        "id",
        "user",
        "query",
        "entity_types",
        "result_count",
        "duration_ms",
        "ip_address",
        "created_at",
    )
