from django.test import TestCase
from privacy_tools.techniques.secure_mpc import SecureMultiPartyComputation


class TestSecureMultiPartyComputation(TestCase):
    def setUp(self):
        self.mpc = SecureMultiPartyComputation(num_parties=3, threshold=2)
        self.secret = 12345

    def test_generate_shares_count(self):
        shares = self.mpc.generate_shares(self.secret)
        self.assertEqual(len(shares), 3)

    def test_reconstruct_secret_with_threshold(self):
        shares = self.mpc.generate_shares(self.secret)
        reconstructed = self.mpc.reconstruct_secret(shares[:2])
        self.assertEqual(reconstructed, self.secret)

    def test_reconstruct_fails_below_threshold(self):
        shares = self.mpc.generate_shares(self.secret)
        with self.assertRaises(ValueError):
            self.mpc.reconstruct_secret(shares[:1])

    def test_secure_sum_correct(self):
        result = self.mpc.secure_sum([10, 20, 30])
        self.assertEqual(result, 60)

    def test_secure_average_correct(self):
        result = self.mpc.secure_average([10, 20, 30])
        self.assertEqual(result, 20)

    def test_joint_signature(self):
        from ecdsa import SigningKey, SECP256k1
        keys = [SigningKey.generate(curve=SECP256k1) for _ in range(2)]
        result = self.mpc.joint_signature(b"test message", keys)
        self.assertIn('signature', result)
        self.assertEqual(result['num_signers'], 2)

    def test_verify_joint_signature(self):
        from ecdsa import SigningKey, SECP256k1, VerifyingKey
        keys = [SigningKey.generate(curve=SECP256k1) for _ in range(2)]
        pubs = [k.get_verifying_key() for k in keys]
        sig = self.mpc.joint_signature(b"test message", keys)
        result = self.mpc.verify_joint_signature(b"test message", sig, pubs)
        self.assertTrue(result)

    def test_evaluate_privacy(self):
        result = self.mpc.evaluate_privacy(num_parties=5, threshold=3, num_computations=10)
        self.assertIn('privacy_score', result)
        self.assertEqual(result['num_parties'], 5)
        self.assertEqual(result['technique'], 'Secure Multi-Party Computation')


class TestSecureMPCEdgeCases(TestCase):
    def test_threshold_one(self):
        mpc = SecureMultiPartyComputation(num_parties=3, threshold=1)
        secret = 9999
        shares = mpc.generate_shares(secret)
        reconstructed = mpc.reconstruct_secret(shares[:1])
        self.assertEqual(reconstructed, secret)

    def test_threshold_one_secure_sum(self):
        mpc = SecureMultiPartyComputation(num_parties=3, threshold=1)
        result = mpc.secure_sum([10, 20, 30])
        self.assertEqual(result, 60)

    def test_threshold_one_evaluate_privacy(self):
        mpc = SecureMultiPartyComputation(num_parties=3, threshold=1)
        result = mpc.evaluate_privacy(num_parties=3, threshold=1, num_computations=5)
        self.assertIn('privacy_score', result)
        self.assertEqual(result['threshold'], 1)
