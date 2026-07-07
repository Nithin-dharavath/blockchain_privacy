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
    path('audit/', views.admin_audit_logs, name='audit_logs'),
    path('audit/user/<int:pk>/', views.admin_audit_user, name='audit_user'),
    path('audit/object/<str:content_type>/<int:pk>/', views.admin_audit_object, name='audit_object'),
    path('notifications/', views.admin_notifications, name='notifications'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/unread-count/', views.unread_notifications_count, name='unread_notifications_count'),
]
