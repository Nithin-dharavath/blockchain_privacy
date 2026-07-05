from django.urls import path
from . import views

app_name = "audit"

urlpatterns = [
    path("", views.audit_log_list, name="list"),
    path("<int:pk>/", views.audit_log_detail, name="detail"),
    path("object-history/", views.audit_object_history, name="object_history"),
]
