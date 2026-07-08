from django.urls import path
from . import views

app_name = 'share'

urlpatterns = [
    path('experiment/create/<int:experiment_id>/', views.create_share_link, name='create_experiment_share'),
    path('experiment/<uuid:token>/', views.shared_experiment_view, name='experiment_shared_view'),
    path('experiment/<int:experiment_id>/links/', views.manage_links, name='manage_experiment_links'),
    path('experiment/links/<int:share_pk>/revoke/', views.revoke_link, name='revoke_experiment_link'),
]
