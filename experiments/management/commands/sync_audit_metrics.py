from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta
import logging

logger = logging.getLogger("experiments")


class Command(BaseCommand):
    help = "Recalculate system metrics from raw experiment data and backfill AuditLog"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Number of days to analyze (default: 30)")
        parser.add_argument("--dry-run", action="store_true", help="Show calculations without storing")

    def handle(self, *args, **options):
        from experiments.models import Experiment
        from admin_panel.models import SystemMetric
        from audit.models import AuditLog

        days = options["days"]
        dry_run = options["dry_run"]
        now = timezone.now()
        since = now - timedelta(days=days)

        self.stdout.write(f"Analyzing data from the last {days} days (since {since.date()})")

        # Total experiments
        total = Experiment.objects.filter(created_at__gte=since).count()
        # Completed
        completed = Experiment.objects.filter(
            created_at__gte=since, status="completed"
        ).count()
        # Failed
        failed = Experiment.objects.filter(
            created_at__gte=since, status="failed"
        ).count()
        # Avg scores
        completed_qs = Experiment.objects.filter(
            created_at__gte=since, status="completed"
        )
        avg_privacy = completed_qs.aggregate(
            avg=Avg("privacy_score")
        )["avg"] or 0.0
        avg_accuracy = completed_qs.aggregate(
            avg=Avg("accuracy")
        )["avg"] or 0.0
        avg_exec = completed_qs.aggregate(
            avg=Avg("execution_time")
        )["avg"] or 0.0

        success_rate = (completed / total * 100) if total else 0.0
        error_rate = (failed / total * 100) if total else 0.0

        # Audit log count
        audit_count = AuditLog.objects.filter(timestamp__gte=since).count()

        self.stdout.write(f"  Total experiments: {total}")
        self.stdout.write(f"  Completed: {completed}")
        self.stdout.write(f"  Failed: {failed}")
        self.stdout.write(f"  Success rate: {success_rate:.1f}%")
        self.stdout.write(f"  Error rate: {error_rate:.1f}%")
        self.stdout.write(f"  Avg privacy score: {avg_privacy:.2f}")
        self.stdout.write(f"  Avg accuracy: {avg_accuracy:.4f}")
        self.stdout.write(f"  Avg execution time: {avg_exec:.3f}s")
        self.stdout.write(f"  Audit log entries: {audit_count}")

        if not dry_run:
            metrics = [
                ("experiment_count", float(total)),
                ("completed_count", float(completed)),
                ("failed_count", float(failed)),
                ("success_rate", round(success_rate, 2)),
                ("error_rate", round(error_rate, 2)),
                ("avg_privacy_score", round(float(avg_privacy), 4)),
                ("avg_accuracy", round(float(avg_accuracy), 4)),
                ("avg_execution_time", round(float(avg_exec), 4)),
                ("audit_log_count", float(audit_count)),
            ]
            for name, value in metrics:
                SystemMetric.objects.create(metric_name=name, metric_value=value)
            self.stdout.write(self.style.SUCCESS(f"Stored {len(metrics)} system metrics"))
        else:
            self.stdout.write(self.style.WARNING("Dry run — no metrics stored"))
