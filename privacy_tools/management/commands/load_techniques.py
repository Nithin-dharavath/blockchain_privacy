from django.core.management.base import BaseCommand
from privacy_tools.models import PrivacyTechnique

class Command(BaseCommand):
    help = 'Load initial privacy techniques'
    
    def handle(self, *args, **kwargs):
        techniques = [
            {
                'name': 'Ring Signatures',
                'technique_type': 'ring_signature',
                'description': 'Ring signatures provide anonymity by allowing a user to sign on behalf of a group without revealing which member signed.',
                'algorithm_details': 'Implements LSAG (Linkable Spontaneous Anonymous Group) signatures using elliptic curve cryptography.',
                'parameters': {'default_ring_size': 5, 'min_ring_size': 3, 'max_ring_size': 50},
                'complexity': 'O(n) where n is ring size',
                'security_level': 8,
                'is_active': True
            },
            {
                'name': 'Zero-Knowledge Proofs',
                'technique_type': 'zkp',
                'description': 'ZKP allows proving knowledge of information without revealing the information itself.',
                'algorithm_details': 'Discrete logarithm-based proofs using elliptic curve BN128.',
                'parameters': {'proof_type': 'discrete_log', 'security_bits': 128},
                'complexity': 'O(1) verification',
                'security_level': 10,
                'is_active': True
            },
            {
                'name': 'Secure Multi-Party Computation',
                'technique_type': 'smpc',
                'description': 'SMPC enables multiple parties to jointly compute functions while keeping inputs private.',
                'algorithm_details': 'Uses Shamir Secret Sharing with threshold cryptography.',
                'parameters': {'default_parties': 3, 'default_threshold': 2},
                'complexity': 'O(n²) where n is number of parties',
                'security_level': 9,
                'is_active': True
            },
            {
                'name': 'Trusted Execution Environment',
                'technique_type': 'tee',
                'description': 'TEE provides hardware-isolated execution environment for secure computation.',
                'algorithm_details': 'Simulates Intel SGX-style secure enclaves with sealed storage.',
                'parameters': {'enclave_memory_mb': 128, 'attestation_enabled': True},
                'complexity': 'O(1) with hardware overhead',
                'security_level': 9,
                'is_active': True
            },
            {
                'name': 'Cryptocurrency Mixer',
                'technique_type': 'mixer',
                'description': 'Mixers break transaction linkability by pooling and redistributing funds.',
                'algorithm_details': 'Multi-hop routing with amount splitting and time delays.',
                'parameters': {'default_pool_size': 10, 'min_delay': 1, 'max_delay': 10},
                'complexity': 'O(n*m) where n is pool size, m is hops',
                'security_level': 7,
                'is_active': True
            }
        ]
        
        for tech_data in techniques:
            technique, created = PrivacyTechnique.objects.get_or_create(
                name=tech_data['name'],
                defaults=tech_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {technique.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {technique.name}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded all privacy techniques!'))
