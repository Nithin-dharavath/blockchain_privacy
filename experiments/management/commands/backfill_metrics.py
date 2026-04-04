from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = 'Backfill accuracy and privacy_score for existing Experiment rows'

    def handle(self, *args, **options):
        import math
        from experiments.models import Experiment
        from privacy_tools.techniques.ring_signature import RingSignature
        from privacy_tools.techniques.zero_knowledge_proof import ZeroKnowledgeProof
        from privacy_tools.techniques.secure_mpc import SecureMultiPartyComputation
        from privacy_tools.techniques.trusted_execution import TrustedExecutionEnvironment
        from privacy_tools.techniques.crypto_mixer import CryptocurrencyMixer

        total = Experiment.objects.count()
        self.stdout.write(f'Total experiments: {total}')

        stats_before = {
            'accuracy_none': Experiment.objects.filter(accuracy__isnull=True).count(),
            'privacy_none': Experiment.objects.filter(privacy_score__isnull=True).count(),
        }
        self.stdout.write(f"Before: {stats_before}")

        updated = 0
        with transaction.atomic():
            for exp in Experiment.objects.select_for_update():
                m = exp.metrics or {}

                # Try to infer successful and total operations from metrics
                succ = None
                tot = None

                for key in ('successful_operations','successful_proofs','successful_computations','successful_mixes','successful_signatures','num_mixed'):
                    if key in m:
                        try:
                            succ = int(m[key])
                            break
                        except Exception:
                            pass

                for key in ('total_operations','total_proofs','total_computations','total_mixed','total_operations'):
                    if key in m:
                        try:
                            tot = int(m[key])
                            break
                        except Exception:
                            pass

                # Fallback to experiment fields
                if succ is None and hasattr(exp, 'successful_operations'):
                    succ = getattr(exp, 'successful_operations', None)

                if tot is None and hasattr(exp, 'total_operations'):
                    tot = getattr(exp, 'total_operations', None)

                # Compute accuracy
                new_accuracy = None
                if tot is not None and tot > 0 and succ is not None:
                    new_accuracy = round(max(0.0, min(1.0, float(succ) / float(tot))), 4)

                # Only update if it was null or differs
                changed = False
                if exp.accuracy is None and new_accuracy is not None:
                    exp.accuracy = new_accuracy
                    changed = True

                # Recompute privacy score using technique evaluator when possible
                technique = exp.privacy_technique
                new_privacy = None
                try:
                    ttype = technique.technique_type
                    if ttype == 'ring_signature':
                        ring_size = m.get('ring_size') or exp.configuration.get('ring_size', None) or exp.anonymity_set_size or 5
                        total_ops = tot or (m.get('total_operations') or exp.metrics.get('total_operations') if isinstance(exp.metrics, dict) else None) or 10
                        new_privacy = RingSignature(ring_size=ring_size).evaluate_privacy(ring_size, total_ops)['privacy_score']
                    elif ttype == 'zkp':
                        num_proofs = m.get('total_operations') or exp.configuration.get('num_proofs', 50)
                        avg_size = m.get('avg_proof_size_kb') or m.get('proof_size_kb') or 0.1
                        new_privacy = ZeroKnowledgeProof().evaluate_privacy(num_proofs, avg_size)['privacy_score']
                    elif ttype == 'smpc':
                        num_parties = exp.configuration.get('num_parties', 3)
                        threshold = exp.configuration.get('threshold', 2)
                        num_comp = m.get('total_operations') or exp.configuration.get('num_computations', 20)
                        new_privacy = SecureMultiPartyComputation(num_parties=num_parties, threshold=threshold).evaluate_privacy(num_parties, threshold, num_comp)['privacy_score']
                    elif ttype == 'tee':
                        num_ops = m.get('total_operations') or exp.configuration.get('num_operations', 50)
                        data_mb = exp.configuration.get('data_size_mb', 1)
                        new_privacy = TrustedExecutionEnvironment().evaluate_privacy(num_ops, data_mb)['privacy_score']
                    elif ttype == 'mixer':
                        pool_size = exp.configuration.get('pool_size', 10)
                        num_tx = m.get('total_operations') or exp.configuration.get('num_transactions', 50)
                        new_privacy = CryptocurrencyMixer(pool_size=pool_size).evaluate_privacy(num_tx, pool_size)['privacy_score']
                except Exception as e:
                    # If evaluation fails, skip
                    new_privacy = None

                if exp.privacy_score is None and new_privacy is not None:
                    exp.privacy_score = float(new_privacy)
                    changed = True

                if changed:
                    exp.save()
                    updated += 1

        stats_after = {
            'accuracy_none': Experiment.objects.filter(accuracy__isnull=True).count(),
            'privacy_none': Experiment.objects.filter(privacy_score__isnull=True).count(),
        }
        self.stdout.write(f'Updated: {updated}')
        self.stdout.write(f'After: {stats_after}')
