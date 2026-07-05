from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Delete audit logs older than a specified number of days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Delete logs older than N days (default: 90)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        from audit.models import AuditLog

        days = options["days"]
        dry_run = options["dry_run"]

        cutoff = timezone.now() - timedelta(days=days)
        qs = AuditLog.objects.filter(timestamp__lt=cutoff)
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(f"No audit logs older than {days} days found."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} audit log(s) older than {days} days "
                    f"(before {cutoff.strftime('%Y-%m-%d %H:%M:%S')})."
                )
            )
            return

        qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {count} audit log(s) older than {days} days."
            )
        )
