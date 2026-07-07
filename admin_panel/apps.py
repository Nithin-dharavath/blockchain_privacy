from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_panel"

    def ready(self):
        from .signals import connect_notification_signals
        connect_notification_signals()
