from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('techniques/', views.techniques_overview, name='techniques'),
]
