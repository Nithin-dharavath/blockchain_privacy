from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:pk>/toggle/', views.toggle_user_approval, name='toggle_user'),
    path('datasets/', views.manage_datasets, name='manage_datasets'),
    path('datasets/<int:pk>/approve/', views.approve_dataset, name='approve_dataset'),
    path('techniques/', views.manage_techniques, name='manage_techniques'),
    path('techniques/add/', views.add_technique, name='add_technique'),
    path('techniques/<int:pk>/edit/', views.edit_technique, name='edit_technique'),
    path('techniques/<int:pk>/toggle/', views.toggle_technique, name='toggle_technique'),
    path('reports/', views.system_reports, name='system_reports'),
]
