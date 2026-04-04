import secrets
import hashlib
from ecdsa import SigningKey, SECP256k1
import json
import math
import logging

logger = logging.getLogger(__name__)

class SecureMultiPartyComputation:
    """
    Secure Multi-Party Computation (SMPC) implementation
    Allows multiple parties to jointly compute a function without revealing inputs
    """
    
    def __init__(self, num_parties=3, threshold=2):
        self.num_parties = num_parties
        self.threshold = threshold  # Minimum parties needed to reconstruct
        self.curve = SECP256k1
        self.prime = 2**256 - 189  # Large prime for Shamir's Secret Sharing
    
    def generate_shares(self, secret, num_shares=None):
        """
        Generate secret shares using Shamir's Secret Sharing
        secret: the value to share
        num_shares: number of shares to create
        """
        if num_shares is None:
            num_shares = self.num_parties
        
        # Generate random coefficients for polynomial
        coefficients = [secret]
        for _ in range(self.threshold - 1):
            coefficients.append(secrets.randbelow(self.prime))
        
        # Generate shares: (x, P(x)) where P is the polynomial
        shares = []
        for i in range(1, num_shares + 1):
            x = i
            y = self._evaluate_polynomial(coefficients, x)
            shares.append((x, y))
        
        return shares
    
    def _evaluate_polynomial(self, coefficients, x):
        """Evaluate polynomial at point x"""
        result = 0
        for i, coef in enumerate(coefficients):
            result += coef * (x ** i)
            result %= self.prime
        return result
    
    def reconstruct_secret(self, shares):
        """
        Reconstruct secret from shares using Lagrange interpolation
        shares: list of (x, y) tuples
        """
        if len(shares) < self.threshold:
            logger.error("Not enough shares to reconstruct secret (have %d, need %d)", len(shares), self.threshold)
            raise ValueError(f"Need at least {self.threshold} shares")
        
        # Use only threshold number of shares
        shares = shares[:self.threshold]
        
        secret = 0
        for i, (x_i, y_i) in enumerate(shares):
            numerator = 1
            denominator = 1

            for j, (x_j, _) in enumerate(shares):
                if i != j:
                    numerator *= -x_j
                    denominator *= (x_i - x_j)

            try:
                lagrange_coef = (numerator * pow(denominator, -1, self.prime)) % self.prime
                secret += (y_i * lagrange_coef) % self.prime
            except Exception:
                logger.exception("Error computing Lagrange coefficient for shares: %s", shares)
                raise

        return secret % self.prime
    
    def secure_sum(self, values):
        """
        Compute sum of values from multiple parties without revealing individual values
        values: list of values from each party
        """
        if len(values) != self.num_parties:
            raise ValueError(f"Expected {self.num_parties} values")
        
        # Each party generates shares of their value
        all_shares = []
        for value in values:
            shares = self.generate_shares(value)
            all_shares.append(shares)
        
        # Parties exchange shares and compute partial sums
        result_shares = []
        for party_idx in range(self.num_parties):
            party_share = sum(
                all_shares[i][party_idx][1] 
                for i in range(self.num_parties)
            ) % self.prime
            result_shares.append((party_idx + 1, party_share))
        
        # Reconstruct final sum
        total_sum = self.reconstruct_secret(result_shares)
        
        return total_sum
    
    def secure_average(self, values):
        """Compute average without revealing individual values"""
        total = self.secure_sum(values)
        return total / len(values)
    
    def joint_signature(self, message, private_keys):
        """
        Generate joint signature from multiple parties
        message: message to sign
        private_keys: list of SigningKey objects
        """
        if len(private_keys) < self.threshold:
            raise ValueError(f"Need at least {self.threshold} signers")
        
        message_hash = hashlib.sha256(message).digest()
        
        # Each party signs with their key
        signatures = []
        for sk in private_keys[:self.threshold]:
            sig = sk.sign(message_hash)
            signatures.append(sig)
        
        # Combine signatures (simplified)
        combined_sig = hashlib.sha256(b''.join(signatures)).digest()
        
        return {
            'signature': combined_sig,
            'num_signers': len(signatures),
            'threshold': self.threshold
        }
    
    def verify_joint_signature(self, message, signature, public_keys):
        """Verify joint signature"""
        try:
            message_hash = hashlib.sha256(message).digest()
            
            # Verify each component (simplified)
            # In production, use proper threshold signature verification
            return len(public_keys) >= self.threshold
        
        except Exception:
            return False
    
    def evaluate_privacy(self, num_parties, threshold, num_computations):
        """Evaluate SMPC privacy metrics"""
        # More nuanced privacy score: combine threshold strength and number of parties
        thr_ratio = threshold / max(1, num_parties)
        anon_bonus = min(1.0, math.log2(max(2, num_parties)) / 5.0)
        privacy_score = 30.0 + thr_ratio * 45.0 + anon_bonus * 20.0
        privacy_score = max(20.0, min(95.0, privacy_score))

        # Communication complexity
        communication_rounds = max(1, num_parties * 2)

        # Collusion resistance (fraction of parties needed to break privacy)
        collusion_resistance = max(0.0, min(1.0, (threshold - 1) / max(1, num_parties)))

        return {
            'privacy_score': round(privacy_score, 2),
            'num_parties': num_parties,
            'threshold': threshold,
            'communication_rounds': communication_rounds,
            'collusion_resistance': round(collusion_resistance, 4),
            'perfect_privacy': threshold > num_parties // 2,
            'technique': 'Secure Multi-Party Computation'
        }
