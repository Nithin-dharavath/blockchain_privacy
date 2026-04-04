import hashlib
import secrets
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging

logger = logging.getLogger(__name__)

class TrustedExecutionEnvironment:
    """
    Simulated Trusted Execution Environment (TEE) for secure computation
    In production, this would use Intel SGX or ARM TrustZone
    """
    
    def __init__(self):
        self.enclave_key = Fernet.generate_key()
        self.cipher = Fernet(self.enclave_key)
        self.attestation_key = secrets.token_bytes(32)
        self.enclave_id = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        self.measurements = []
    
    def create_enclave(self, code_hash):
        """
        Create a secure enclave
        code_hash: hash of the code to be executed in the enclave
        """
        enclave_data = {
            'enclave_id': self.enclave_id,
            'code_hash': code_hash,
            'creation_time': str(secrets.randbits(64)),
            'security_version': '1.0'
        }
        
        # Sign enclave with attestation key
        attestation = self._generate_attestation(enclave_data)
        
        return {
            'enclave_id': self.enclave_id,
            'attestation': attestation,
            'status': 'created'
        }
    
    def _generate_attestation(self, enclave_data):
        """Generate remote attestation for enclave"""
        data_str = json.dumps(enclave_data, sort_keys=True).encode()
        attestation_hash = hashlib.sha256(
            data_str + self.attestation_key
        ).hexdigest()
        
        return attestation_hash
    
    def seal_data(self, data):
        """
        Seal data inside enclave (encrypt with enclave key)
        Data can only be unsealed by this enclave
        """
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            data = json.dumps(data).encode()
        
        sealed_data = self.cipher.encrypt(data)
        
        # Add measurement
        measurement = hashlib.sha256(sealed_data).hexdigest()
        self.measurements.append(measurement)
        
        return {
            'sealed_data': base64.b64encode(sealed_data).decode(),
            'measurement': measurement,
            'enclave_id': self.enclave_id
        }
    
    def unseal_data(self, sealed_package):
        """Unseal data from enclave"""
        try:
            sealed_data = base64.b64decode(sealed_package['sealed_data'])
            
            # Verify enclave ID
            if sealed_package['enclave_id'] != self.enclave_id:
                raise ValueError("Data sealed by different enclave")
            
            # Decrypt
            unsealed_data = self.cipher.decrypt(sealed_data)
            
            return unsealed_data.decode()
        
        except Exception as e:
            logger.exception("Failed to unseal data")
            raise ValueError(f"Failed to unseal data: {str(e)}")
    
    def secure_compute(self, function_code, encrypted_input):
        """
        Execute computation in secure enclave
        function_code: code to execute
        encrypted_input: encrypted input data
        """
        # Unseal input
        input_data = self.unseal_data(encrypted_input)
        
        # Execute computation (simplified simulation)
        # In real TEE, this would execute in hardware-protected memory
        try:
            # Parse input
            data = json.loads(input_data)
            
            # Simulate secure computation
            if function_code == 'sum':
                result = sum(data.get('values', []))
            elif function_code == 'average':
                values = data.get('values', [])
                result = sum(values) / len(values) if values else 0
            elif function_code == 'hash':
                result = hashlib.sha256(
                    json.dumps(data).encode()
                ).hexdigest()
            else:
                result = "Computation completed"
            
            # Seal result
            sealed_result = self.seal_data({'result': result})

            return sealed_result
        
        except Exception as e:
            logger.exception("Secure compute failed")
            raise ValueError(f"Computation failed: {str(e)}")
    
    def remote_attestation(self, challenge):
        """
        Perform remote attestation to prove enclave integrity
        challenge: random challenge from verifier
        """
        # Create attestation report
        report = {
            'enclave_id': self.enclave_id,
            'measurements': self.measurements[-5:],  # Last 5 measurements
            'challenge': challenge,
            'security_version': '1.0'
        }
        
        # Sign report
        report_str = json.dumps(report, sort_keys=True).encode()
        signature = hashlib.sha256(
            report_str + self.attestation_key
        ).hexdigest()
        
        return {
            'report': report,
            'signature': signature
        }
    
    def verify_attestation(self, attestation, expected_challenge):
        """Verify remote attestation"""
        try:
            report = attestation['report']
            signature = attestation['signature']
            
            # Verify challenge
            if report['challenge'] != expected_challenge:
                return False
            
            # Verify signature
            report_str = json.dumps(report, sort_keys=True).encode()
            expected_sig = hashlib.sha256(
                report_str + self.attestation_key
            ).hexdigest()
            
            ok = signature == expected_sig
            if not ok:
                logger.warning("Attestation signature mismatch")
            return ok
        
        except Exception:
            logger.exception("Attestation verification exception")
            return False
    
    def evaluate_privacy(self, num_operations, data_size_mb):
        """Evaluate TEE privacy metrics"""
        # TEE provides strong protection but not perfect — account for measurements and overhead
        overhead_percent = 10  # Typical TEE overhead
        measurements = len(self.measurements)

        # Base score reduced slightly if few measurements (less attestation evidence)
        base = 80.0
        measurement_bonus = min(15.0, measurements * 1.5)
        overhead_penalty = min(15.0, overhead_percent * 0.3)

        privacy_score = base + measurement_bonus - overhead_penalty
        privacy_score = max(40.0, min(95.0, privacy_score))

        security_properties = {
            'memory_encryption': True,
            'isolated_execution': True,
            'remote_attestation': True,
            'sealed_storage': True
        }

        return {
            'privacy_score': round(privacy_score, 2),
            'hardware_isolated': True,
            'performance_overhead_percent': overhead_percent,
            'security_properties': security_properties,
            'enclave_id': self.enclave_id,
            'num_measurements': measurements,
            'technique': 'Trusted Execution Environment'
        }
