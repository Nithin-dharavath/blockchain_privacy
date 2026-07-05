import json
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Export audit logs to a JSON file with optional date filtering"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            type=str,
            default=None,
            help="Start date (YYYY-MM-DD). If omitted, no lower bound.",
        )
        parser.add_argument(
            "--end",
            type=str,
            default=None,
            help="End date (YYYY-MM-DD). If omitted, no upper bound.",
        )
        parser.add_argument(
            "--out",
            type=str,
            default="audit_export.json",
            help="Output file path (default: audit_export.json)",
        )

    def _parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."
            )

    def handle(self, *args, **options):
        from audit.models import AuditLog

        start_str = options["start"]
        end_str = options["end"]
        out_file = options["out"]

        qs = AuditLog.objects.all().order_by("timestamp")

        try:
            if start_str:
                start_date = self._parse_date(start_str)
                start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
                qs = qs.filter(timestamp__gte=start_dt)

            if end_str:
                end_date = self._parse_date(end_str)
                end_dt = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
                qs = qs.filter(timestamp__lte=end_dt)
        except ValueError as e:
            raise CommandError(str(e))

        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("No audit logs found for the specified filters."))
            return

        logs = []
        for log in qs:
            logs.append({
                "id": log.id,
                "user": log.user.username if log.user else None,
                "action_type": log.action_type,
                "content_type": log.content_type,
                "object_id": log.object_id,
                "object_repr": log.object_repr,
                "changes": log.changes,
                "ip_address": log.ip_address,
                "request_method": log.request_method,
                "url": log.url,
                "timestamp": log.timestamp.isoformat(),
            })

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {count} audit log(s) to {out_file}"
            )
        )
