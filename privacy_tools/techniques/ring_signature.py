import hashlib
import secrets
from ecdsa import SigningKey, SECP256k1, VerifyingKey
from ecdsa.util import sigencode_string, sigdecode_string
import math
import json
import logging

logger = logging.getLogger(__name__)

class RingSignature:
    """
    Implementation of Ring Signatures for blockchain privacy
    Based on LSAG (Linkable Spontaneous Anonymous Group) signatures
    """
    
    def __init__(self, ring_size=5):
        self.ring_size = ring_size
        self.curve = SECP256k1
        
    def generate_key_pair(self):
        """Generate a new key pair"""
        private_key = SigningKey.generate(curve=self.curve)
        public_key = private_key.get_verifying_key()
        return private_key, public_key
    
    def generate_ring(self, signer_public_key, num_decoys=4):
        """Generate a ring of public keys including the signer and decoys"""
        ring = [signer_public_key]
        
        for _ in range(num_decoys):
            _, decoy_public_key = self.generate_key_pair()
            ring.append(decoy_public_key)
        
        # Shuffle for anonymity
        import random
        random.shuffle(ring)
        
        return ring
    
    def sign(self, message, private_key, public_key_ring):
        """
        Create a ring signature
        message: bytes to sign
        private_key: signer's private key
        public_key_ring: list of public keys in the ring
        """
        message_hash = hashlib.sha256(message).digest()
        
        # Find signer position in ring
        signer_public_key = private_key.get_verifying_key()
        signer_index = None
        for i, pk in enumerate(public_key_ring):
            if pk.to_string() == signer_public_key.to_string():
                signer_index = i
                break
        
        if signer_index is None:
            raise ValueError("Signer's public key not in ring")
        
        n = len(public_key_ring)
        
        # Generate random values for all positions except signer
        randoms = []
        for i in range(n):
            if i == signer_index:
                randoms.append(None)
            else:
                randoms.append(secrets.randbits(256))
        
        # Create ring signature components
        c = [None] * n
        s = randoms.copy()
        
        # Start with random initial value
        c[(signer_index + 1) % n] = int.from_bytes(
            hashlib.sha256(message_hash + secrets.token_bytes(32)).digest(),
            'big'
        )
        
        # Complete the ring (except signer position)
        for i in range(1, n):
            idx = (signer_index + i) % n
            next_idx = (idx + 1) % n
            
            if idx != signer_index:
                # Hash previous c value with random
                hash_input = message_hash + c[idx].to_bytes(32, 'big') + s[idx].to_bytes(32, 'big')
                c[next_idx] = int.from_bytes(hashlib.sha256(hash_input).digest(), 'big')
        
        # Close the ring at signer position
        # Sign with actual private key
        actual_signature = private_key.sign(
            message,
            sigencode=sigencode_string,
            hashfunc=hashlib.sha256
        )
        s[signer_index] = int.from_bytes(actual_signature[:32], 'big')
        
        signature = {
            'c0': c[0],
            's_values': s,
            'ring_size': n
        }
        
        return signature
    
    def verify(self, message, signature, public_key_ring):
        """Verify a ring signature"""
        try:
            message_hash = hashlib.sha256(message).digest()
            n = signature['ring_size']
            
            if len(public_key_ring) != n:
                return False
            
            c = [None] * n
            c[0] = signature['c0']
            s_values = signature['s_values']
            # Verify ring
            for i in range(n):
                next_idx = (i + 1) % n
                hash_input = message_hash + c[i].to_bytes(32, 'big') + s_values[i].to_bytes(32, 'big')
                c[next_idx] = int.from_bytes(hashlib.sha256(hash_input).digest(), 'big')
            
            # Check if ring closes
            ok = c[0] == signature['c0']
            if not ok:
                logger.debug("Ring does not close: expected %s got %s", signature['c0'], c[0])
            return ok
        
        except Exception as e:
            logger.exception("Exception occurred during ring signature verification")
            return False
    
    def evaluate_privacy(self, ring_size, num_transactions):
        """
        Evaluate privacy metrics for ring signature
        Returns anonymity set size and unlinkability score
        """
        anonymity_set = ring_size
        unlinkability_score = 1.0 - (1.0 / ring_size)
        # More realistic scoring: logarithmic gains from anonymity set and unlinkability
        anon_factor = min(1.0, math.log2(max(1, ring_size) + 1) / 6.0)
        unlink_factor = max(0.0, min(1.0, unlinkability_score))

        base = 45.0
        privacy_score = base + anon_factor * 35 + unlink_factor * 20
        privacy_score = max(20.0, min(95.0, privacy_score))

        return {
            'anonymity_set_size': anonymity_set,
            'unlinkability_score': round(unlinkability_score, 4),
            'privacy_score': round(privacy_score, 2),
            'technique': 'Ring Signatures'
        }
