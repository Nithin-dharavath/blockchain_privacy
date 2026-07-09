from datetime import datetime, date
from uuid import UUID
from django.db import models


class AuditableMixin(models.Model):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_state = self._get_field_dict()

    def _get_field_dict(self):
        result = {}
        deferred = self.get_deferred_fields()
        for field in self._meta.fields:
            name = field.name
            if name == "id" or name in deferred:
                continue
            if field.is_relation and hasattr(field, "attname"):
                value = getattr(self, field.attname)
            else:
                value = getattr(self, name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            elif isinstance(value, UUID):
                value = str(value)
            result[name] = value
        return result

    def _get_changes(self):
        new_state = self._get_field_dict()
        old_state = getattr(self, "_original_state", {})
        changes = {}
        for key in old_state:
            old_val = old_state[key]
            new_val = new_state.get(key)
            if old_val != new_val:
                changes[key] = {"old": old_val, "new": new_val}
        return changes

    def _get_audit_user(self):
        for attr in ("user", "uploaded_by"):
            if hasattr(self, attr):
                val = getattr(self, attr)
                if val is not None:
                    return val
        return None

    def _get_special_action(self, changes):
        model_name = self._meta.model_name
        if model_name == "experiment" and "status" in changes:
            s = changes["status"]
            if s["old"] in ("pending", "running") and s["new"] in ("running", "completed", "failed"):
                return "RUN"
        if model_name == "dataset" and "status" in changes:
            s = changes["status"]
            if s["old"] == "pending" and s["new"] == "approved":
                return "APPROVE"
            if s["old"] == "pending" and s["new"] == "rejected":
                return "REJECT"
        return None

    def _log_audit(self, action_type, changes):
        from audit.models import AuditLog

        AuditLog.objects.create(
            user=self._get_audit_user(),
            action_type=action_type,
            content_type=self._meta.model_name,
            object_id=self.pk,
            object_repr=str(self)[:255],
            changes=changes,
        )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self._log_audit("CREATE", {})
        else:
            changes = self._get_changes()
            if changes:
                action = self._get_special_action(changes) or "UPDATE"
                self._log_audit(action, changes)
        self._original_state = self._get_field_dict()

    def delete(self, *args, **kwargs):
        self._log_audit("DELETE", {})
        super().delete(*args, **kwargs)
