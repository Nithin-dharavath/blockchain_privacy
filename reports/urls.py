from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('generate/', views.report_generate, name='generate'),
    path('<int:pk>/', views.report_detail, name='detail'),
    path('<int:pk>/download/', views.report_download, name='download'),
    path('<int:pk>/delete/', views.report_delete, name='delete'),
    # Report scheduling
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:pk>/toggle/', views.schedule_toggle, name='schedule_toggle'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
]
