from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

class Command(BaseCommand):
    help = 'Re-run experiments in batch and generate a CSV report of before/after metrics'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='Limit number of experiments to rerun (most recent)')
        parser.add_argument('--out', type=str, default='rerun_report.csv', help='Output CSV filename')
        parser.add_argument('--force', action='store_true', help='Force rerun even if completed')

    def handle(self, *args, **options):
        import csv
        from experiments.models import Experiment
        from experiments.experiment_runner import PrivacyExperimentRunner

        limit = options.get('limit')
        out_file = options.get('out')
        force = options.get('force')

        qs = Experiment.objects.all().order_by('-created_at')
        if limit:
            qs = qs[:limit]

        rows = []
        total = qs.count()
        self.stdout.write(f'Preparing to rerun {total} experiments')

        with transaction.atomic():
            for exp in qs:
                if exp.status == 'running':
                    self.stdout.write(f'Skipping {exp.pk} (running)')
                    continue
                if exp.status == 'completed' and not force:
                    self.stdout.write(f'Skipping {exp.pk} (completed) — use --force to override')
                    continue

                prev_privacy = exp.privacy_score
                prev_accuracy = exp.accuracy

                try:
                    df = exp.dataset.get_data()
                    if df is None or len(df) == 0:
                        self.stdout.write(f'Skipping {exp.pk}: empty dataset')
                        continue
                except Exception as e:
                    self.stdout.write(f'Failed to load dataset for {exp.pk}: {e}')
                    continue

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

                    rows.append({
                        'id': exp.pk,
                        'name': exp.name,
                        'technique': exp.privacy_technique.technique_type,
                        'prev_privacy': prev_privacy,
                        'new_privacy': exp.privacy_score,
                        'prev_accuracy': prev_accuracy,
                        'new_accuracy': exp.accuracy,
                    })

                    self.stdout.write(f'Reran {exp.pk}')

                except Exception as e:
                    exp.status = 'failed'
                    exp.error_message = str(e)
                    exp.completed_at = timezone.now()
                    exp.save()
                    self.stdout.write(f'Failed {exp.pk}: {e}')

        # Write CSV
        with open(out_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id','name','technique','prev_privacy','new_privacy','prev_accuracy','new_accuracy']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        self.stdout.write(f'Wrote report to {out_file} with {len(rows)} rows')
