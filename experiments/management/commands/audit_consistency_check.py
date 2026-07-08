from django.core.management.base import BaseCommand
from django.db import models
from django.apps import apps


class Command(BaseCommand):
    help = "Verify all FK relationships are intact and report orphaned records"

    def add_arguments(self, parser):
        parser.add_argument("--fix", action="store_true", help="Delete orphaned records found")

    def handle(self, *args, **options):
        should_fix = options["fix"]
        checks = [
            ("experiments", "Experiment", "user", "accounts", "User"),
            ("experiments", "Experiment", "dataset", "datasets", "Dataset"),
            ("experiments", "Experiment", "privacy_technique", "privacy_tools", "PrivacyTechnique"),
            ("datasets", "Dataset", "uploaded_by", "accounts", "User"),
            ("reports", "Report", "user", "accounts", "User"),
            ("reports", "Report", "template", "reports", "ReportTemplate"),
            ("notifications", "Notification", "recipient", "accounts", "User"),
            ("audit", "AuditLog", "user", "accounts", "User"),
        ]

        total_orphans = 0
        for app_label, model_name, fk_field, target_app, target_model in checks:
            try:
                model = apps.get_model(app_label, model_name)
                target = apps.get_model(target_app, target_model)
                fk_field_obj = model._meta.get_field(fk_field)
                if fk_field_obj.is_relation and fk_field_obj.many_to_many:
                    continue
                fk_attname = fk_field_obj.attname if hasattr(fk_field_obj, "attname") else fk_field
                existing_pks = set(target.objects.values_list("pk", flat=True))
                orphans = model.objects.exclude(**{f"{fk_attname}__in": existing_pks}).exclude(
                    **{f"{fk_attname}__isnull": True}
                )
                count = orphans.count()
                if count:
                    self.stdout.write(
                        self.style.WARNING(
                            f"{model_name}.{fk_field}: {count} orphaned record(s)"
                        )
                    )
                    total_orphans += count
                    if should_fix:
                        deleted, _ = orphans.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f"  → Deleted {deleted} orphaned record(s)")
                        )
                else:
                    self.stdout.write(f"{model_name}.{fk_field}: OK")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error checking {model_name}.{fk_field}: {e}"))

        if total_orphans == 0:
            self.stdout.write(self.style.SUCCESS("All FK relationships intact — no orphans found."))
        elif not should_fix:
            self.stdout.write(
                self.style.WARNING(
                    f"{total_orphans} total orphan(s) found. Run with --fix to delete them."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Fixed {total_orphans} orphaned record(s)."))
