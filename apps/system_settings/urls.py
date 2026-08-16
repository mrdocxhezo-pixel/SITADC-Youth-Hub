"""URL configuration for System Settings (Phase 28)."""

from django.urls import path
from . import views

app_name = 'system_settings'

urlpatterns = [
    path('', views.system_settings_list, name='system_settings_list'),
    path('create/', views.system_settings_create, name='system_settings_create'),
    path('<int:pk>/update/', views.system_settings_update, name='system_settings_update'),
    path('<int:pk>/delete/', views.system_settings_delete, name='system_settings_delete'),
    path('<int:pk>/', views.system_settings_detail, name='system_settings_detail'),
]