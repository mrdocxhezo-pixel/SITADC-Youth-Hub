"""Views for System Settings (Phase 28)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import (
    SystemConfiguration,
)
from .forms import (
    SystemConfigurationForm,
)

# Generic view functions for CRUD operations
def object_list(request, model, template_name, context_name, paginate_by=25):
    """Generic list view for a model."""
    queryset = model.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    paginator = Paginator(queryset, paginate_by)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        context_name: page_obj,
        'search_query': search_query,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, template_name, context)

def object_create(request, model_form, success_url, success_message, template_name='system_settings/object_form.html'):
    """Generic create view for a model."""
    if request.method == 'POST':
        form = model_form(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = model_form()
    context = {
        'form': form,
        'list_url': success_url,
    }
    return render(request, template_name, context)

def object_update(request, model, model_form, pk, success_url, success_message, template_name='system_settings/object_form.html'):
    """Generic update view for a model."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        form = model_form(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = model_form(instance=obj)
    context = {
        'form': form,
        'object': obj,
        'list_url': success_url,
    }
    return render(request, template_name, context)

def object_delete(request, model, pk, success_url, success_message, template_name='system_settings/object_confirm_delete.html'):
    """Generic delete view for a model."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, success_message)
        return redirect(success_url)
    context = {
        'object': obj,
        'list_url': success_url,
        'model_name': model._meta.verbose_name,
    }
    return render(request, template_name, context)

def object_detail(request, model, pk, list_url, template_name, context_name):
    """Generic detail view for a model."""
    obj = get_object_or_404(model, pk=pk)
    context = {
        context_name: obj,
        'list_url': list_url,
    }
    return render(request, template_name, context)

# System Settings Views
@login_required
def system_settings_list(request):
    return object_list(request, SystemConfiguration, 'system_settings/system_settings_list.html', 'system_settings')

@login_required
def system_settings_create(request):
    return object_create(
        request,
        SystemConfigurationForm,
        'system_settings:system_settings_list',
        'System setting created successfully.'
    )

@login_required
def system_settings_update(request, pk):
    return object_update(
        request,
        SystemConfiguration,
        SystemConfigurationForm,
        pk,
        'system_settings:system_settings_list',
        'System setting updated successfully.'
    )

@login_required
def system_settings_delete(request, pk):
    return object_delete(
        request,
        SystemConfiguration,
        pk,
        'system_settings:system_settings_list',
        'System setting deleted successfully.'
    )

@login_required
def system_settings_detail(request, pk):
    return object_detail(
        request,
        SystemConfiguration,
        pk,
        'system_settings:system_settings_list',
        'system_settings/system_settings_detail.html',
        'system_setting'
    )
