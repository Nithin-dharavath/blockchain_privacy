from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta


class Command(BaseCommand):
    help = 'Record system-wide metrics (active_users, experiments_per_hour, avg_response_time, error_rate) into SystemMetric'

    def handle(self, *args, **options):
        from admin_panel.models import SystemMetric
        from accounts.models import User
        from experiments.models import Experiment

        now = timezone.now()

        # active_users — users who created an experiment in the last 24h
        active_users = (
            User.objects
            .filter(experiments__created_at__gte=now - timedelta(hours=24))
            .distinct()
            .count()
        )
        SystemMetric.objects.create(
            metric_name='active_users',
            metric_value=float(active_users),
        )
        self.stdout.write(f'active_users: {active_users}')

        # experiments_per_hour — experiments created in the last hour
        one_hour_ago = now - timedelta(hours=1)
        exp_count = Experiment.objects.filter(
            created_at__gte=one_hour_ago
        ).count()
        SystemMetric.objects.create(
            metric_name='experiments_per_hour',
            metric_value=float(exp_count),
        )
        self.stdout.write(f'experiments_per_hour: {exp_count}')

        # avg_response_time — approximated as avg execution_time of recent completed experiments
        recent_completed = Experiment.objects.filter(
            status='completed',
            completed_at__gte=now - timedelta(hours=24),
            execution_time__isnull=False,
        )
        avg_resp = recent_completed.aggregate(
            avg=Avg('execution_time')
        )['avg'] or 0.0
        SystemMetric.objects.create(
            metric_name='avg_response_time',
            metric_value=round(float(avg_resp), 4),
        )
        self.stdout.write(f'avg_response_time: {avg_resp}')

        # error_rate — percentage of experiments that failed in the last 24h
        last_24h = now - timedelta(hours=24)
        total_last_24h = Experiment.objects.filter(
            created_at__gte=last_24h
        ).count()
        failed_last_24h = Experiment.objects.filter(
            created_at__gte=last_24h,
            status='failed',
        ).count()
        error_rate = (failed_last_24h / total_last_24h * 100) if total_last_24h > 0 else 0.0
        SystemMetric.objects.create(
            metric_name='error_rate',
            metric_value=round(error_rate, 2),
        )
        self.stdout.write(f'error_rate: {error_rate}%')

        self.stdout.write(self.style.SUCCESS('System metrics recorded successfully.'))
