import json
import logging
from django.db import models
from django.core.management.base import BaseCommand

logger = logging.getLogger("experiments")


class Command(BaseCommand):
    help = "Fix null accuracy scores, recalculate report summaries, and repair data issues"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
        parser.add_argument("--fix-accuracy", action="store_true", help="Fix null/zero accuracy from metrics")
        parser.add_argument("--fix-summaries", action="store_true", help="Recalculate report summaries")
        parser.add_argument("--all", action="store_true", help="Run all fixes")

    def handle(self, *args, **options):
        from experiments.models import Experiment
        from reports.models import Report

        dry_run = options["dry_run"]
        run_all = options["all"]
        fix_accuracy = run_all or options["fix_accuracy"]
        fix_summaries = run_all or options["fix_summaries"]

        total_fixed = 0

        # --- Fix accuracy ---
        if fix_accuracy:
            self.stdout.write("--- Fixing null/zero accuracy scores ---")
            qs = Experiment.objects.filter(status="completed").filter(
                models.Q(accuracy__isnull=True) | models.Q(accuracy=0)
            )
            count = qs.count()
            self.stdout.write(f"Found {count} experiment(s) with missing accuracy")
            if not dry_run:
                fixed = 0
                for exp in qs:
                    if exp.metrics and isinstance(exp.metrics, dict):
                        total_ops = exp.metrics.get("total_operations", 0)
                        successful = exp.metrics.get("successful_operations", 0)
                        if total_ops > 0:
                            exp.accuracy = successful / total_ops
                            exp.save(update_fields=["accuracy"])
                            fixed += 1
                    if exp.privacy_score is not None and (exp.accuracy is None or exp.accuracy == 0):
                        exp.accuracy = exp.privacy_score / 100.0
                        exp.save(update_fields=["accuracy"])
                        fixed += 1
                self.stdout.write(self.style.SUCCESS(f"Fixed {fixed} experiment(s)"))
                total_fixed += fixed

        # --- Fix report summaries ---
        if fix_summaries:
            self.stdout.write("--- Recalculating report summaries ---")
            reports = Report.objects.filter(summary__isnull=True) | Report.objects.filter(summary="")
            count = reports.count()
            self.stdout.write(f"Found {count} report(s) with empty summaries")
            if not dry_run:
                fixed = 0
                for report in reports:
                    try:
                        content_data = json.loads(report.content)
                    except (json.JSONDecodeError, TypeError):
                        content_data = {}
                    summary = content_data.get("executive_summary", "")
                    if summary:
                        report.summary = summary
                        report.save(update_fields=["summary"])
                        fixed += 1
                    else:
                        experiments = report.experiments.all()
                        if experiments:
                            names = ", ".join(e.name for e in experiments[:3])
                            report.summary = f"Report for {len(experiments)} experiment(s): {names}"
                            report.save(update_fields=["summary"])
                            fixed += 1
                self.stdout.write(self.style.SUCCESS(f"Fixed {fixed} report(s)"))
                total_fixed += fixed

        if total_fixed:
            self.stdout.write(self.style.SUCCESS(f"\nTotal records fixed: {total_fixed}"))
        else:
            self.stdout.write(self.style.WARNING("No fixes were applied."))
