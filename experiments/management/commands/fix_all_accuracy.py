from django.core.management.base import BaseCommand
from experiments.models import Experiment


class Command(BaseCommand):
    help = 'Fix accuracy values for all completed experiments'

    def handle(self, *args, **options):
        experiments = Experiment.objects.filter(status='completed')
        
        fixed_count = 0
        for exp in experiments:
            # Check if accuracy is None or 0
            if exp.accuracy is None or exp.accuracy == 0:
                # Try to calculate from metrics
                if exp.metrics and isinstance(exp.metrics, dict):
                    total = exp.metrics.get('total_operations', 0)
                    successful = exp.metrics.get('successful_operations', 0)
                    
                    if total > 0:
                        exp.accuracy = successful / total
                        exp.save()
                        fixed_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Fixed {exp.name}: {successful}/{total} = {exp.accuracy:.4f}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipped {exp.name}: No operation data in metrics'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipped {exp.name}: No metrics available'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully fixed {fixed_count} experiments')
        )
