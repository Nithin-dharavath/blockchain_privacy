from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_redirect, name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('datasets/', include('datasets.urls')),
    path('experiments/', include('experiments.urls')),
    path('reports/', include('reports.urls')),
    path('audit/', include('audit.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('notifications/', include('notifications.urls')),
    path('export/', include('export.urls')),
    path('share/', include('share.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
