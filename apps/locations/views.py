"""
Views for the geographic locations module.

Provides:
  * JSON API endpoints used by cascading dropdowns across the whole system.
  * CRUD management views (authorized) for maintaining the hierarchy.

JSON endpoints accept ``?parent_id=`` and return
``[{"id": ..., "name": ...}]`` suitable for dynamic dropdown population.
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
)

from .models import (
    Constituency,
    Country,
    District,
    Province,
    Ward,
)
from .serializers import (
    constituency_json,
    country_json,
    district_json,
    province_json,
    ward_json,
)

logger = logging.getLogger(__name__)


class JsonLocationView(View):
    """Base view returning a lightweight JSON list of geographic records."""

    model = None
    parent_param = None
    serializer = None
    active_only = True

    def get_parent_id(self):
        return None

    def get_queryset(self):
        qs = self.model.objects.select_related()
        parent_id = self.get_parent_id()
        if parent_id and self.parent_param:
            qs = qs.filter(**{self.parent_param: parent_id})
        if self.active_only:
            qs = qs.filter(is_active=True)
        return qs.order_by("sort_order", "name")

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        serializer = self.__class__.serializer
        items = [serializer(obj) for obj in self.get_queryset()]
        return JsonResponse(items, safe=False)


class CountriesJsonView(JsonLocationView):
    model = Country
    serializer = country_json


class ProvincesJsonView(JsonLocationView):
    model = Province
    parent_param = "country_id"
    serializer = province_json

    def get_parent_id(self):
        return self.request.GET.get("country_id")


class DistrictsJsonView(JsonLocationView):
    model = District
    parent_param = "province_id"
    serializer = district_json

    def get_parent_id(self):
        return self.request.GET.get("province_id") or self.request.GET.get(
            "parent_id"
        )


class ConstituenciesJsonView(JsonLocationView):
    model = Constituency
    parent_param = "district_id"
    serializer = constituency_json

    def get_parent_id(self):
        return self.request.GET.get("district_id") or self.request.GET.get(
            "parent_id"
        )


class WardsJsonView(JsonLocationView):
    model = Ward
    parent_param = "constituency_id"
    serializer = ward_json

    def get_parent_id(self):
        return self.request.GET.get("constituency_id") or self.request.GET.get(
            "parent_id"
        )


# ---------------------------------------------------------------------------
# Management views (authorized) - CRUD for the hierarchy.
# ---------------------------------------------------------------------------


class CountryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Country
    template_name = "locations/country_list.html"
    context_object_name = "countries"
    ordering = ("sort_order", "name")
    permission_required = "locations.view_country"

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search"] = self.request.GET.get("q", "").strip()
        ctx["province_count"] = Province.objects.count()
        ctx["district_count"] = District.objects.count()
        ctx["constituency_count"] = Constituency.objects.count()
        ctx["ward_count"] = Ward.objects.count()
        return ctx


class CountryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Country
    fields = ["name", "code", "sort_order", "is_active"]
    template_name = "locations/country_form.html"
    success_url = reverse_lazy("locations:country_list")
    permission_required = "locations.add_country"


class CountryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Country
    fields = ["name", "code", "sort_order", "is_active"]
    template_name = "locations/country_form.html"
    success_url = reverse_lazy("locations:country_list")
    permission_required = "locations.change_country"


class ProvinceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Province
    template_name = "locations/province_list.html"
    context_object_name = "provinces"
    permission_required = "locations.view_province"

    def get_queryset(self):
        qs = super().get_queryset().select_related("country")
        country_id = self.request.GET.get("country")
        search = self.request.GET.get("q", "").strip()
        if country_id:
            qs = qs.filter(country_id=country_id)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs.order_by("country", "sort_order", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["countries"] = Country.objects.order_by("name")
        ctx["country"] = self.request.GET.get("country", "")
        ctx["search"] = self.request.GET.get("q", "").strip()
        return ctx


class ProvinceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Province
    fields = ["country", "name", "code", "sort_order", "is_active"]
    template_name = "locations/province_form.html"
    success_url = reverse_lazy("locations:province_list")
    permission_required = "locations.add_province"


class ProvinceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Province
    fields = ["country", "name", "code", "sort_order", "is_active"]
    template_name = "locations/province_form.html"
    success_url = reverse_lazy("locations:province_list")
    permission_required = "locations.change_province"


class DistrictListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = District
    template_name = "locations/district_list.html"
    context_object_name = "districts"
    permission_required = "locations.view_district"

    def get_queryset(self):
        qs = super().get_queryset().select_related("province", "province__country")
        province_id = self.request.GET.get("province")
        country_id = self.request.GET.get("country")
        search = self.request.GET.get("q", "").strip()
        if country_id:
            qs = qs.filter(province__country_id=country_id)
        if province_id:
            qs = qs.filter(province_id=province_id)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs.order_by("province", "sort_order", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["countries"] = Country.objects.order_by("name")
        ctx["provinces"] = Province.objects.order_by("name")
        ctx["country"] = self.request.GET.get("country", "")
        ctx["province"] = self.request.GET.get("province", "")
        ctx["search"] = self.request.GET.get("q", "").strip()
        return ctx


class DistrictCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = District
    fields = ["province", "name", "code", "sort_order", "is_active"]
    template_name = "locations/district_form.html"
    success_url = reverse_lazy("locations:district_list")
    permission_required = "locations.add_district"


class DistrictUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = District
    fields = ["province", "name", "code", "sort_order", "is_active"]
    template_name = "locations/district_form.html"
    success_url = reverse_lazy("locations:district_list")
    permission_required = "locations.change_district"


class ConstituencyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Constituency
    template_name = "locations/constituency_list.html"
    context_object_name = "constituencies"
    permission_required = "locations.view_constituency"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("district", "district__province")
        )
        district_id = self.request.GET.get("district")
        province_id = self.request.GET.get("province")
        search = self.request.GET.get("q", "").strip()
        if province_id:
            qs = qs.filter(district__province_id=province_id)
        if district_id:
            qs = qs.filter(district_id=district_id)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs.order_by("district", "sort_order", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["provinces"] = Province.objects.order_by("name")
        ctx["districts"] = District.objects.order_by("name")
        ctx["province"] = self.request.GET.get("province", "")
        ctx["district"] = self.request.GET.get("district", "")
        ctx["search"] = self.request.GET.get("q", "").strip()
        return ctx


class ConstituencyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Constituency
    fields = ["district", "name", "code", "sort_order", "is_active"]
    template_name = "locations/constituency_form.html"
    success_url = reverse_lazy("locations:constituency_list")
    permission_required = "locations.add_constituency"


class ConstituencyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Constituency
    fields = ["district", "name", "code", "sort_order", "is_active"]
    template_name = "locations/constituency_form.html"
    success_url = reverse_lazy("locations:constituency_list")
    permission_required = "locations.change_constituency"


class WardListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Ward
    template_name = "locations/ward_list.html"
    context_object_name = "wards"
    permission_required = "locations.view_ward"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("constituency", "constituency__district")
        )
        constituency_id = self.request.GET.get("constituency")
        district_id = self.request.GET.get("district")
        province_id = self.request.GET.get("province")
        search = self.request.GET.get("q", "").strip()
        if province_id:
            qs = qs.filter(constituency__district__province_id=province_id)
        if district_id:
            qs = qs.filter(constituency__district_id=district_id)
        if constituency_id:
            qs = qs.filter(constituency_id=constituency_id)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs.order_by("constituency", "sort_order", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["provinces"] = Province.objects.order_by("name")
        ctx["districts"] = District.objects.order_by("name")
        ctx["constituencies"] = Constituency.objects.order_by("name")
        ctx["province"] = self.request.GET.get("province", "")
        ctx["district"] = self.request.GET.get("district", "")
        ctx["constituency"] = self.request.GET.get("constituency", "")
        ctx["search"] = self.request.GET.get("q", "").strip()
        return ctx


class WardCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Ward
    fields = ["constituency", "name", "code", "sort_order", "is_active"]
    template_name = "locations/ward_form.html"
    success_url = reverse_lazy("locations:ward_list")
    permission_required = "locations.add_ward"


class WardUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Ward
    fields = ["constituency", "name", "code", "sort_order", "is_active"]
    template_name = "locations/ward_form.html"
    success_url = reverse_lazy("locations:ward_list")
    permission_required = "locations.change_ward"
