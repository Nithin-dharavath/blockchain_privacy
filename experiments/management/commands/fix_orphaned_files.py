import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger("error")


class Command(BaseCommand):
    help = "Clean up media files that have no corresponding database records"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show orphaned files without deleting")
        parser.add_argument("--all", action="store_true", help="Check all upload directories (default: datasets + reports only)")

    def handle(self, *args, **options):
        from datasets.models import Dataset
        from reports.models import Report

        dry_run = options["dry_run"]
        check_all = options["all"]

        media_root = settings.MEDIA_ROOT
        if not os.path.isdir(media_root):
            self.stdout.write(self.style.ERROR(f"MEDIA_ROOT does not exist: {media_root}"))
            return

        total_orphans = 0
        total_size = 0

        # Collect all DB-tracked file paths
        db_files = set()
        for ds in Dataset.objects.exclude(file="").exclude(file__isnull=True):
            try:
                db_files.add(os.path.normpath(ds.file.path))
            except Exception:
                pass

        for report in Report.objects.exclude(file="").exclude(file__isnull=True):
            try:
                db_files.add(os.path.normpath(report.file.path))
            except Exception:
                pass

        self.stdout.write(f"Tracking {len(db_files)} file(s) referenced in database")

        # Walk upload directories and find orphans
        check_dirs = ["datasets", "reports"]
        if check_all:
            check_dirs = [
                d for d in os.listdir(media_root)
                if os.path.isdir(os.path.join(media_root, d))
            ]

        for subdir in check_dirs:
            dir_path = os.path.join(media_root, subdir)
            if not os.path.isdir(dir_path):
                continue
            for root, dirs, files in os.walk(dir_path):
                for fname in files:
                    fpath = os.path.normpath(os.path.join(root, fname))
                    if fpath not in db_files:
                        fsize = os.path.getsize(fpath)
                        total_orphans += 1
                        total_size += fsize
                        rel_path = os.path.relpath(fpath, media_root)
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(f"[DRY RUN] Orphan: {rel_path} ({fsize} bytes)")
                            )
                        else:
                            try:
                                os.remove(fpath)
                                self.stdout.write(
                                    self.style.SUCCESS(f"Deleted orphan: {rel_path} ({fsize} bytes)")
                                )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f"Failed to delete {rel_path}: {e}")
                                )

                # Remove empty directories
                if not dry_run:
                    for dirpath, dirnames, filenames in os.walk(dir_path, topdown=False):
                        if dirpath == dir_path:
                            continue
                        try:
                            if not os.listdir(dirpath):
                                os.rmdir(dirpath)
                                rel = os.path.relpath(dirpath, media_root)
                                self.stdout.write(f"Removed empty directory: {rel}")
                        except Exception:
                            pass

        if total_orphans == 0:
            self.stdout.write(self.style.SUCCESS("No orphaned files found."))
        else:
            size_mb = total_size / (1024 * 1024)
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"Found {total_orphans} orphaned file(s) ({size_mb:.2f} MB). "
                        "Run without --dry-run to delete."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Cleaned up {total_orphans} orphaned file(s) ({size_mb:.2f} MB)."
                    )
                )
