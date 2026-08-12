"""Views for the Enterprise Search module.

Every view enforces permissions server-side; search results are acquired
through the permission-scaled providers so confidentiality cannot leak.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, View

from .constants import DEFAULT_RESULTS_PER_TYPE
from .exceptions import SearchPermissionDenied, SearchValidationError
from .forms import GlobalSearchForm, SavedSearchForm
from .models import SavedSearch
from .permissions import user_can_export, user_can_manage
from .selectors import (
    available_entity_type_choices,
    query_logs,
    recent_searches_for_user,
    saved_searches_for_user,
    user_can_access_search,
)
from .services import create_saved_search, delete_saved_search, run_search

logger = logging.getLogger(__name__)


def _require_search_permission(user) -> None:
    if not user_can_access_search(user):
        raise PermissionDenied(_("You do not have permission to search."))


def _client_ip(request: HttpRequest) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def build_export_query_string(request: HttpRequest) -> str:
    """Serialize the current search GET parameters for the export URL."""
    from urllib.parse import urlencode

    params = []
    q = request.GET.get("q", "").strip()
    if q:
        params.append(("q", q))
    for key in request.GET.getlist("types"):
        params.append(("types", key))
    return urlencode(params)


class SearchHomeView(TemplateView):
    """The unified search page with grouped results."""

    template_name = "search/search.html"

    def dispatch(self, request, *args, **kwargs):
        _require_search_permission(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        entity_keys = request.GET.getlist("types") or None
        form = GlobalSearchForm(request.GET or None, user=request.user)
        context["search_form"] = form
        context["saved_form"] = SavedSearchForm()

        results = None
        if form.is_valid():
            query = form.cleaned_data.get("q") or ""
            types = form.cleaned_data.get("types") or entity_keys
            per_type = form.cleaned_data.get("per_type") or DEFAULT_RESULTS_PER_TYPE
            if query:
                try:
                    results = run_search(
                        request.user,
                        query,
                        types,
                        results_per_type=per_type,
                        ip_address=_client_ip(request),
                    )
                except SearchValidationError as exc:
                    messages.error(
                        request, exc.messages[0] if exc.messages else "Search error"
                    )
                except SearchPermissionDenied as exc:
                    messages.error(request, str(exc))

        context["results"] = results
        context["entity_choices"] = available_entity_type_choices(request.user)
        context["recent_searches"] = recent_searches_for_user(request.user)
        context["saved_searches"] = saved_searches_for_user(request.user)
        context["can_export"] = user_can_export(request.user)
        context["active_query"] = request.GET.get("q", "")
        context["export_query_string"] = build_export_query_string(request)
        return context


class ExportSearchView(TemplateView):
    """CSV export of a current search (requires search.export)."""

    template_name = "search/search.html"

    def dispatch(self, request, *args, **kwargs):
        if not user_can_export(request.user):
            raise PermissionDenied(
                _("You do not have permission to export search results.")
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        from .exports import build_csv_response

        query = request.GET.get("q", "").strip()
        types = request.GET.getlist("types") or None
        try:
            results = run_search(
                request.user,
                query,
                types,
                persist=False,
                ip_address=_client_ip(request),
            )
        except (SearchValidationError, SearchPermissionDenied) as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
            return redirect(reverse("search:home"))
        return build_csv_response(results)


class SavedSearchListView(TemplateView):
    """List the actor's saved searches."""

    template_name = "search/saved_search_list.html"

    def dispatch(self, request, *args, **kwargs):
        _require_search_permission(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["saved_searches"] = saved_searches_for_user(self.request.user)
        context["search_url"] = reverse("search:home")
        return context


class SavedSearchCreateView(View):
    """Save the current query as a named search."""

    def post(self, request, *args, **kwargs):
        _require_search_permission(request.user)
        form = SavedSearchForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Invalid saved search request."))
            return redirect(request.POST.get("next") or reverse("search:home"))
        name = form.cleaned_data.get("name", "").strip()
        query = form.cleaned_data.get("query", "").strip()
        types_raw = form.cleaned_data.get("types", "")
        types = [part.strip() for part in types_raw.split(",") if part.strip()] or None
        try:
            create_saved_search(
                request.user, name=name, query=query, entity_types=types
            )
            messages.success(
                request, _("Saved search %(name)s created.") % {"name": name}
            )
        except (SearchValidationError, SearchPermissionDenied) as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        return redirect(request.POST.get("next") or reverse("search:home"))


class SavedSearchDeleteView(View):
    """Delete a saved search owned by the actor."""

    def post(self, request, pk, *args, **kwargs):
        _require_search_permission(request.user)
        saved = get_object_or_404(SavedSearch, pk=pk)
        try:
            delete_saved_search(request.user, saved)
            messages.success(request, _("Saved search deleted."))
        except SearchPermissionDenied as exc:
            messages.error(request, str(exc))
        return redirect(reverse("search:saved_list"))


class SavedSearchRunView(View):
    """Re-run a saved search and land on the results page."""

    def get(self, request, pk, *args, **kwargs):
        _require_search_permission(request.user)
        saved = get_object_or_404(SavedSearch, pk=pk)
        if saved.user_id != request.user.id:
            raise PermissionDenied(_("You may only run your own saved searches."))
        query_params = [("q", saved.query)]
        for key in saved.entity_types:
            query_params.append(("types", key))
        return redirect(f"{reverse('search:home')}?{self._urlencode(query_params)}")

    @staticmethod
    def _urlencode(pairs) -> str:
        from urllib.parse import urlencode

        return urlencode(pairs)


class SearchAuditView(TemplateView):
    """Read-only audit trail of executed queries (search.manage)."""

    template_name = "search/audit_log.html"

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage(request.user):
            raise PermissionDenied(
                _("You do not have permission to view the search audit log.")
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logs"] = query_logs(self.request.user)
        return context
