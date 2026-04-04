from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

class Command(BaseCommand):
    help = 'Re-run experiments to recompute metrics using the current implementations'

    def add_arguments(self, parser):
        parser.add_argument('--ids', type=str, help='Comma-separated experiment IDs to rerun')
        parser.add_argument('--limit', type=int, default=5, help='Number of recent experiments to rerun when --ids not provided')
        parser.add_argument('--force', action='store_true', help='Force rerun even if experiment is completed')

    def handle(self, *args, **options):
        from experiments.models import Experiment
        from experiments.experiment_runner import PrivacyExperimentRunner
        import pandas as pd

        ids = options.get('ids')
        limit = options.get('limit') or 5
        force = options.get('force')

        if ids:
            try:
                id_list = [int(x.strip()) for x in ids.split(',') if x.strip()]
            except Exception:
                self.stdout.write(self.style.ERROR('Invalid --ids format'))
                return
            q = Experiment.objects.filter(pk__in=id_list).order_by('-created_at')
        else:
            q = Experiment.objects.all().order_by('-created_at')[:limit]

        total = q.count()
        self.stdout.write(f'Found {total} experiments to rerun')

        re_runs = []
        with transaction.atomic():
            for exp in q:
                if exp.status == 'running':
                    self.stdout.write(f'Skipping {exp.pk} (status=running)')
                    continue
                if exp.status == 'completed' and not force:
                    self.stdout.write(f'Skipping {exp.pk} (already completed) — use --force to override')
                    continue

                self.stdout.write(f'Re-running experiment {exp.pk}: "{exp.name}" (technique: {exp.privacy_technique.technique_type})')

                # Load dataset
                try:
                    df = exp.dataset.get_data()
                    if df is None or len(df) == 0:
                        self.stdout.write(self.style.WARNING(f'Experiment {exp.pk} skipped: dataset empty'))
                        continue
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to load dataset for exp {exp.pk}: {e}'))
                    continue

                # preserve previous values for reporting
                prev_privacy = exp.privacy_score
                prev_accuracy = exp.accuracy

                # run
                try:
                    exp.status = 'running'
                    exp.started_at = timezone.now()
                    exp.save()

                    runner = PrivacyExperimentRunner(exp, df)
                    results = runner.run()

                    exp.privacy_score = results.get('privacy_score')
                    exp.execution_time = results.get('execution_time')
                    exp.accuracy = results.get('accuracy')
                    exp.throughput = results.get('throughput')
                    exp.anonymity_set_size = results.get('anonymity_set_size')
                    exp.metrics = results.get('metrics') or results

                    exp.status = 'completed'
                    exp.completed_at = timezone.now()
                    exp.save()

                    re_runs.append({
                        'id': exp.pk,
                        'name': exp.name,
                        'technique': exp.privacy_technique.technique_type,
                        'prev_privacy': prev_privacy,
                        'new_privacy': exp.privacy_score,
                        'prev_accuracy': prev_accuracy,
                        'new_accuracy': exp.accuracy,
                    })

                    self.stdout.write(self.style.SUCCESS(f'Completed {exp.pk}'))

                except Exception as e:
                    exp.status = 'failed'
                    exp.error_message = str(e)
                    exp.completed_at = timezone.now()
                    exp.save()
                    self.stdout.write(self.style.ERROR(f'Experiment {exp.pk} failed: {e}'))

        # Summary
        self.stdout.write('\nRe-run summary:')
        for r in re_runs:
            self.stdout.write(f"ID {r['id']}: {r['name']} ({r['technique']}) — privacy: {r['prev_privacy']} -> {r['new_privacy']}, accuracy: {r['prev_accuracy']} -> {r['new_accuracy']}")
