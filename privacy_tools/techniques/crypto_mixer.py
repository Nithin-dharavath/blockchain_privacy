import hashlib
import secrets
import random
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)

class CryptocurrencyMixer:
    """
    Cryptocurrency Mixer (Tumbler) implementation for transaction privacy
    Breaks the link between sender and receiver addresses
    """
    
    def __init__(self, pool_size=10, min_delay=1, max_delay=10):
        self.pool_size = pool_size
        self.min_delay = min_delay  # seconds
        self.max_delay = max_delay  # seconds
        self.mixing_pool = []
        self.anonymity_set = []
        self.transaction_graph = defaultdict(list)
    
    def generate_address(self):
        """Generate a random blockchain address"""
        return hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:40]
    
    def create_deposit(self, sender_address, amount, recipient_address):
        """
        Create a deposit for mixing
        sender_address: original sender
        amount: amount to mix
        recipient_address: final destination
        """
        # Generate temporary addresses for mixing
        temp_addresses = [
            self.generate_address() 
            for _ in range(random.randint(2, 5))
        ]
        
        # Create deposit receipt
        deposit = {
            'deposit_id': hashlib.sha256(
                f"{sender_address}{amount}{time.time()}".encode()
            ).hexdigest(),
            'sender': sender_address,
            'amount': amount,
            'recipient': recipient_address,
            'temp_addresses': temp_addresses,
            'timestamp': time.time(),
            'status': 'pending'
        }
        
        # Add to pool
        self.mixing_pool.append(deposit)
        
        return deposit['deposit_id']
    
    def mix_transactions(self):
        """
        Mix transactions in the pool
        Uses multi-hop routing and amount splitting
        """
        if len(self.mixing_pool) < 3:
            return {
                'status': 'insufficient_pool',
                'message': 'Need at least 3 transactions for effective mixing'
            }
        
        # Shuffle pool
        random.shuffle(self.mixing_pool)
        
        mixed_transactions = []
        
        for deposit in self.mixing_pool[:self.pool_size]:
            # Split amount randomly
            amount = deposit['amount']
            num_splits = random.randint(2, 4)
            split_amounts = self._split_amount(amount, num_splits)
            
            # Create mixing routes
            routes = []
            for split_amount in split_amounts:
                route = self._create_mixing_route(
                    deposit['sender'],
                    deposit['recipient'],
                    deposit['temp_addresses'],
                    split_amount
                )
                routes.append(route)
            
            mixed_tx = {
                'deposit_id': deposit['deposit_id'],
                'routes': routes,
                'anonymity_set_size': len(self.mixing_pool),
                'delay': random.uniform(self.min_delay, self.max_delay),
                'status': 'mixed'
            }
            
            mixed_transactions.append(mixed_tx)
            deposit['status'] = 'mixed'
        
        # Update anonymity set
        self.anonymity_set.extend(mixed_transactions)
        
        return {
            'status': 'success',
            'num_mixed': len(mixed_transactions),
            'anonymity_set_size': len(self.anonymity_set)
        }
    
    def _split_amount(self, amount, num_splits):
        """Split amount into random parts"""
        splits = []
        remaining = amount
        
        for i in range(num_splits - 1):
            split = random.uniform(0.1, 0.4) * remaining
            splits.append(round(split, 8))
            remaining -= split
        
        splits.append(round(remaining, 8))
        return splits
    
    def _create_mixing_route(self, sender, recipient, temp_addresses, amount):
        """Create a multi-hop mixing route"""
        route = [sender]
        
        # Add random temporary addresses
        num_hops = random.randint(2, len(temp_addresses))
        selected_temp = random.sample(temp_addresses, num_hops)
        route.extend(selected_temp)
        
        # Add final recipient
        route.append(recipient)
        
        # Create transaction chain
        hops = []
        for i in range(len(route) - 1):
            hop = {
                'from': route[i],
                'to': route[i + 1],
                'amount': amount,
                'delay': random.uniform(self.min_delay, self.max_delay)
            }
            hops.append(hop)
            
            # Track in transaction graph
            self.transaction_graph[route[i]].append(route[i + 1])
        
        return {
            'hops': hops,
            'total_hops': len(hops),
            'path_length': len(route)
        }
    
    def withdraw(self, deposit_id, verification_code):
        """
        Withdraw mixed funds
        deposit_id: original deposit ID
        verification_code: proof of ownership
        """
        # Find deposit
        deposit = None
        for d in self.mixing_pool:
            if d['deposit_id'] == deposit_id:
                deposit = d
                break
        
        if not deposit:
            logger.warning("Withdraw failed: deposit not found: %s", deposit_id)
            return {'status': 'error', 'message': 'Deposit not found'}
        
        if deposit['status'] != 'mixed':
            logger.info("Withdraw attempt before mixing complete for deposit %s (status=%s)", deposit_id, deposit['status'])
            return {'status': 'error', 'message': 'Transaction not yet mixed'}
        
        # Simulate verification
        expected_code = hashlib.sha256(
            deposit['deposit_id'].encode()
        ).hexdigest()[:16]
        
        if verification_code != expected_code:
            logger.warning("Invalid verification code for deposit %s", deposit_id)
            return {'status': 'error', 'message': 'Invalid verification code'}
        
        # Mark as withdrawn
        deposit['status'] = 'withdrawn'
        
        return {
            'status': 'success',
            'recipient': deposit['recipient'],
            'amount': deposit['amount']
        }
    
    def analyze_anonymity(self):
        """Analyze anonymity set and privacy metrics"""
        if not self.anonymity_set:
            return {'anonymity_set_size': 0, 'privacy_score': 0}
        
        # Calculate anonymity set size
        anonymity_set_size = len(set(
            tx['deposit_id'] for tx in self.anonymity_set
        ))
        
        # Calculate average path length
        total_hops = sum(
            route['total_hops']
            for tx in self.anonymity_set
            for route in tx['routes']
        )
        num_routes = sum(len(tx['routes']) for tx in self.anonymity_set)
        avg_path_length = total_hops / num_routes if num_routes > 0 else 0
        
        # More nuanced privacy score: combine anonymity set and path complexity
        anon_component = min(60.0, anonymity_set_size * 3.0)
        path_component = min(25.0, avg_path_length * 3.0)
        privacy_score = 25.0 + anon_component + path_component
        privacy_score = max(20.0, min(95.0, privacy_score))

        return {
            'anonymity_set_size': anonymity_set_size,
            'avg_path_length': round(avg_path_length, 2),
            'total_mixed': len(self.anonymity_set),
            'privacy_score': round(privacy_score, 2)
        }
    
    def evaluate_privacy(self, num_transactions, pool_size):
        """Evaluate mixer privacy metrics"""
        anonymity_analysis = self.analyze_anonymity()
        
        # Calculate unlinkability
        unlinkability = 1.0 - (1.0 / max(pool_size, 1))
        
        # Timing analysis resistance
        timing_resistance = (self.max_delay - self.min_delay) / self.max_delay
        
        return {
            'privacy_score': anonymity_analysis.get('privacy_score', 50),
            'anonymity_set_size': pool_size,
            'unlinkability_score': round(unlinkability, 4),
            'timing_resistance': round(timing_resistance, 4),
            'avg_path_length': anonymity_analysis.get('avg_path_length', 0),
            'mixing_rounds': 1,
            'technique': 'Cryptocurrency Mixer'
        }
