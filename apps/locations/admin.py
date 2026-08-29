"""
Django admin registration for the geographic hierarchy.

Authorized administrators can manage countries, provinces, districts,
constituencies and wards from the standard admin interface: add/edit/activate/
deactivate, search, filter and view the parent-child hierarchy.
"""

from django.contrib import admin

from .models import (
    Constituency,
    Country,
    District,
    Province,
    Ward,
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order", "is_active", "province_count")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("sort_order", "name")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "code", "sort_order", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Provinces")
    def province_count(self, obj):
        return obj.province_count


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0
    fields = ("name", "code", "sort_order", "is_active")
    show_change_link = True


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "code", "sort_order", "is_active", "district_count")
    list_filter = ("country", "is_active")
    search_fields = ("name", "code")
    ordering = ("country", "sort_order", "name")
    list_select_related = ("country",)
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [DistrictInline]

    @admin.display(description="Districts")
    def district_count(self, obj):
        return obj.district_count


class ConstituencyInline(admin.TabularInline):
    model = Constituency
    extra = 0
    fields = ("name", "code", "sort_order", "is_active")
    show_change_link = True


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "code", "sort_order", "is_active", "constituency_count")
    list_filter = ("province__country", "province", "is_active")
    search_fields = ("name", "code")
    ordering = ("province", "sort_order", "name")
    list_select_related = ("province", "province__country")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [ConstituencyInline]

    @admin.display(description="Constituencies")
    def constituency_count(self, obj):
        return obj.constituency_count

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "province", "province__country"
        )


class WardInline(admin.TabularInline):
    model = Ward
    extra = 0
    fields = ("name", "code", "sort_order", "is_active")
    show_change_link = True


@admin.register(Constituency)
class ConstituencyAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "code", "sort_order", "is_active", "ward_count")
    list_filter = ("district__province", "district", "is_active")
    search_fields = ("name", "code")
    ordering = ("district", "sort_order", "name")
    list_select_related = ("district", "district__province")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [WardInline]

    @admin.display(description="Wards")
    def ward_count(self, obj):
        return obj.ward_count

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "district", "district__province"
        )


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ("name", "constituency", "code", "sort_order", "is_active")
    list_filter = ("constituency__district__province", "constituency__district", "is_active")
    search_fields = ("name", "code")
    ordering = ("constituency", "sort_order", "name")
    list_select_related = ("constituency", "constituency__district")
    readonly_fields = ("id", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "constituency", "constituency__district"
        )
