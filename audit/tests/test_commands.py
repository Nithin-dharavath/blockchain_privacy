import json
import os
import tempfile
from io import StringIO
from datetime import timedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from audit.models import AuditLog
from privacy_platform.test_utils import create_user


class PurgeAuditLogsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("auditpurge")
        cls.old_log = AuditLog.objects.create(
            user=cls.user,
            action_type="create",
            content_type="User",
            object_id=cls.user.pk,
            object_repr=cls.user.username,
        )
        AuditLog.objects.filter(pk=cls.old_log.pk).update(
            timestamp=timezone.now() - timedelta(days=100),
        )
        cls.old_log.refresh_from_db()
        cls.new_log = AuditLog.objects.create(
            user=cls.user,
            action_type="update",
            content_type="User",
            object_id=cls.user.pk,
            object_repr=cls.user.username,
        )

    def test_dry_run_shows_count(self):
        out = StringIO()
        call_command("purge_audit_logs", "--days=30", "--dry-run", stdout=out)
        output = out.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("1 audit log", output)

    def test_deletes_old_logs(self):
        out = StringIO()
        call_command("purge_audit_logs", "--days=30", stdout=out)
        with self.assertRaises(AuditLog.DoesNotExist):
            AuditLog.objects.get(pk=self.old_log.pk)
        self.assertIsNotNone(AuditLog.objects.get(pk=self.new_log.pk))

    def test_no_old_logs(self):
        out = StringIO()
        call_command("purge_audit_logs", "--days=200", stdout=out)
        self.assertIsNotNone(AuditLog.objects.get(pk=self.old_log.pk))
        self.assertIsNotNone(AuditLog.objects.get(pk=self.new_log.pk))


class ExportAuditLogsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("exportuser")
        cls.log = AuditLog.objects.create(
            user=cls.user,
            action_type="create",
            content_type="User",
            object_id=cls.user.pk,
            object_repr=cls.user.username,
        )

    def test_exports_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmpfile = f.name
        try:
            out = StringIO()
            call_command("export_audit_logs", f"--out={tmpfile}", stdout=out)
            with open(tmpfile, "r") as fh:
                data = json.load(fh)
            exported_ids = [d["id"] for d in data]
            self.assertIn(self.log.pk, exported_ids)
        finally:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)

    def test_date_filter_no_results(self):
        out = StringIO()
        call_command(
            "export_audit_logs",
            "--start=2020-01-01",
            "--end=2020-01-02",
            stdout=out,
        )
        self.assertIn("No audit logs found", out.getvalue())
