import json
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger("reports")


class Command(BaseCommand):
    help = "Generate reports for completed experiments that have no associated report"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without creating")
        parser.add_argument("--user-id", type=int, help="Only process experiments for a specific user ID")

    def handle(self, *args, **options):
        from experiments.models import Experiment
        from reports.models import Report
        from accounts.models import User

        dry_run = options["dry_run"]
        user_id = options.get("user_id")

        completed = Experiment.objects.filter(status="completed")
        if user_id:
            completed = completed.filter(user_id=user_id)

        generated = 0
        skipped = 0
        for exp in completed:
            has_report = Report.objects.filter(experiments=exp).exists()
            if has_report:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would generate report for Experiment #{exp.id}: {exp.name}")
                generated += 1
                continue

            try:
                content = self._build_report_content(exp)
                report = Report.objects.create(
                    title=f"Report - {exp.name}",
                    report_type="single",
                    user=exp.user,
                    file_format="json",
                    content=json.dumps(content, indent=2),
                    summary=content.get("executive_summary", ""),
                )
                report.experiments.add(exp)
                report.generated_at = timezone.now()
                report.save(update_fields=["generated_at"])
                generated += 1
                self.stdout.write(self.style.SUCCESS(f"Created Report #{report.id} for Experiment #{exp.id}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed for Experiment #{exp.id}: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {generated} report(s) generated, {skipped} already had reports"
            )
        )

    def _build_report_content(self, exp):
        exec_summary = (
            f"Experiment '{exp.name}' completed using {exp.privacy_technique.name} "
            f"with privacy score {exp.privacy_score or 'N/A'} "
            f"and accuracy {exp.accuracy or 'N/A'}."
        )
        return {
            "executive_summary": exec_summary,
            "methodology": [
                {
                    "technique": exp.privacy_technique.name,
                    "type": exp.privacy_technique.technique_type,
                    "description": exp.privacy_technique.description,
                    "config": exp.configuration,
                }
            ],
            "results": [
                {
                    "experiment_id": exp.id,
                    "name": exp.name,
                    "status": exp.status,
                    "privacy_score": exp.privacy_score,
                    "accuracy": exp.accuracy,
                    "execution_time": exp.execution_time,
                    "throughput": exp.throughput,
                    "anonymity_set_size": exp.anonymity_set_size,
                    "metrics": exp.metrics,
                }
            ],
            "comparison": [],
            "recommendations": [
                "Privacy Score: " + ("Good" if (exp.privacy_score or 0) >= 7 else "Consider improvement"),
            ],
            "raw_data": "",
        }
