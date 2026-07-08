import re
from audit.models import AuditLog

EXCLUDED_PATHS = [
    "/static/",
    "/media/",
    "/admin/jsi18n/",
    "/favicon.ico",
]

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

ACTION_OVERRIDES = {
    "/accounts/login/": "LOGIN",
    "/accounts/logout/": "LOGOUT",
}

CONTENT_TYPE_MAP = {
    "experiments": "Experiment",
    "datasets": "Dataset",
    "reports": "Report",
    "accounts": "User",
    "admin-panel": "Admin",
    "dashboard": "Dashboard",
}

ACTION_KEYWORD_MAP = {
    "upload": "CREATE",
    "create": "CREATE",
    "add": "CREATE",
    "generate": "CREATE",
    "bulk_upload": "CREATE",
    "run": "RUN",
    "rerun": "RUN",
    "download": "DOWNLOAD",
    "export": "EXPORT",
    "approve": "APPROVE",
    "reject": "REJECT",
    "toggle": "UPDATE",
    "edit": "UPDATE",
    "delete": "DELETE",
    "remove": "DELETE",
}


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_log(request):
            return self.get_response(request)

        audit_data = self._prepare_audit_data(request)
        response = self.get_response(request)
        self._create_audit_log(request, response, audit_data)
        return response

    def _should_log(self, request):
        if request.method not in MUTATING_METHODS:
            return False
        path = request.path_info
        for excluded in EXCLUDED_PATHS:
            if excluded in path:
                return False
        return True

    def _prepare_audit_data(self, request):
        return {
            "ip_address": self._get_client_ip(request),
            "user_agent": self._get_user_agent(request),
            "action_type": self._infer_action_type(request),
            "content_type": self._infer_content_type(request),
            "object_id": self._extract_object_id(request),
        }

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _get_user_agent(self, request):
        return (request.META.get("HTTP_USER_AGENT") or "")[:500]

    def _infer_action_type(self, request):
        path = request.path_info.rstrip("/")
        method = request.method

        if path in ACTION_OVERRIDES:
            return ACTION_OVERRIDES[path]
        if path + "/" in ACTION_OVERRIDES:
            return ACTION_OVERRIDES[path + "/"]

        segments = path.strip("/").split("/")
        for segment in reversed(segments):
            if segment in ACTION_KEYWORD_MAP:
                return ACTION_KEYWORD_MAP[segment]

        if method == "POST":
            return "CREATE"
        elif method in ("PUT", "PATCH"):
            return "UPDATE"
        elif method == "DELETE":
            return "DELETE"

        return "RUN"

    def _infer_content_type(self, request):
        segments = request.path_info.strip("/").split("/")
        if segments and segments[0] in CONTENT_TYPE_MAP:
            return CONTENT_TYPE_MAP[segments[0]]
        return "Request"

    def _extract_object_id(self, request):
        segments = request.path_info.strip("/").split("/")
        for segment in segments:
            if segment.isdigit():
                return int(segment)
        return 0

    def _resolve_object_repr(self, content_type, object_id):
        """Try to resolve a human-readable representation for the audited object."""
        if not object_id:
            return ""
        model_map = {
            "Experiment": ("experiments", "Experiment"),
            "Dataset": ("datasets", "Dataset"),
            "Report": ("reports", "Report"),
            "User": ("accounts", "User"),
        }
        app_label, model_name = model_map.get(content_type, (None, None))
        if app_label is None:
            return ""
        try:
            from django.apps import apps
            model = apps.get_model(app_label, model_name)
            obj = model.objects.get(pk=object_id)
            return str(obj)[:255]
        except Exception:
            return ""

    def _create_audit_log(self, request, response, audit_data):
        if response.status_code in (302, 303) and "/accounts/login/" in response.get("Location", ""):
            return

        user = request.user if request.user.is_authenticated else None

        try:
            object_repr = self._resolve_object_repr(
                audit_data["content_type"], audit_data["object_id"]
            )
            AuditLog.objects.create(
                user=user,
                action_type=audit_data["action_type"],
                content_type=audit_data["content_type"],
                object_id=audit_data["object_id"],
                object_repr=object_repr,
                changes={
                    "user_agent": audit_data["user_agent"],
                    "status_code": response.status_code,
                },
                ip_address=audit_data["ip_address"],
                request_method=request.method,
                url=request.get_full_path()[:500],
            )
        except Exception:
            pass
