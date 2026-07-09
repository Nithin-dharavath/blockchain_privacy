from django.test import TestCase
from privacy_tools.techniques.trusted_execution import TrustedExecutionEnvironment


class TestTrustedExecutionEnvironment(TestCase):
    def setUp(self):
        self.tee = TrustedExecutionEnvironment()
        self.code_hash = "abc123def456"

    def test_create_enclave(self):
        result = self.tee.create_enclave(self.code_hash)
        self.assertIn('enclave_id', result)
        self.assertIn('attestation', result)
        self.assertEqual(result['status'], 'created')

    def test_seal_unseal_roundtrip(self):
        sealed = self.tee.seal_data("sensitive data")
        unsealed = self.tee.unseal_data(sealed)
        self.assertEqual(unsealed, "sensitive data")

    def test_unseal_fails_wrong_enclave(self):
        sealed = self.tee.seal_data("secret")
        other_tee = TrustedExecutionEnvironment()
        with self.assertRaises(ValueError):
            other_tee.unseal_data(sealed)

    def test_secure_compute_sum(self):
        encrypted_input = self.tee.seal_data({'values': [1, 2, 3, 4, 5]})
        result = self.tee.secure_compute('sum', encrypted_input)
        unsealed = self.tee.unseal_data(result)
        self.assertIn('result', eval(unsealed))
        self.assertEqual(eval(unsealed)['result'], 15)

    def test_secure_compute_average(self):
        encrypted_input = self.tee.seal_data({'values': [10, 20, 30]})
        result = self.tee.secure_compute('average', encrypted_input)
        unsealed = self.tee.unseal_data(result)
        self.assertEqual(eval(unsealed)['result'], 20)

    def test_secure_compute_hash(self):
        encrypted_input = self.tee.seal_data({'data': 'test'})
        result = self.tee.secure_compute('hash', encrypted_input)
        unsealed = self.tee.unseal_data(result)
        self.assertIsInstance(eval(unsealed)['result'], str)

    def test_remote_attestation_verify(self):
        challenge = "random_challenge"
        attestation = self.tee.remote_attestation(challenge)
        self.assertIn('report', attestation)
        self.assertIn('signature', attestation)
        self.assertEqual(attestation['report']['challenge'], challenge)

    def test_verify_attestation_rejects_wrong_challenge(self):
        challenge = "valid_challenge"
        attestation = self.tee.remote_attestation(challenge)
        result = self.tee.verify_attestation(attestation, "wrong_challenge")
        self.assertFalse(result)

    def test_evaluate_privacy(self):
        for i in range(5):
            self.tee.seal_data(f"data_{i}")
        result = self.tee.evaluate_privacy(num_operations=5, data_size_mb=10)
        self.assertIn('privacy_score', result)
        self.assertTrue(result['hardware_isolated'])
        self.assertEqual(result['technique'], 'Trusted Execution Environment')


class TestTrustedExecutionEdgeCases(TestCase):
    def test_evaluate_privacy_zero_data_size(self):
        tee = TrustedExecutionEnvironment()
        result = tee.evaluate_privacy(num_operations=0, data_size_mb=0)
        self.assertIn('privacy_score', result)
        self.assertTrue(result['hardware_isolated'])
        self.assertEqual(result['num_measurements'], 0)

    def test_enclave_with_empty_code_hash(self):
        tee = TrustedExecutionEnvironment()
        result = tee.create_enclave("")
        self.assertIn('enclave_id', result)
        self.assertEqual(result['status'], 'created')
