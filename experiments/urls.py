from django.urls import path
from . import views

app_name = 'experiments'

urlpatterns = [
    path('results/', views.results_dashboard, name='results'),
    path('', views.experiment_list, name='list'),
    path('create/', views.experiment_create, name='create'),
    path('<int:pk>/', views.experiment_detail, name='detail'),
    path('<int:pk>/run/', views.experiment_run, name='run'),
    path('<int:pk>/delete/', views.experiment_delete, name='delete'),
    path('compare/', views.experiment_compare, name='compare'),
    path('comparison/<int:pk>/', views.comparison_detail, name='comparison_detail'),
]
