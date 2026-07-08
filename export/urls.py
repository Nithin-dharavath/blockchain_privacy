from django.urls import path
from . import views

app_name = 'export'

urlpatterns = [
    path('experiments/', views.export_experiments, name='export_experiments'),
    path('reports/', views.export_reports, name='export_reports'),
]
