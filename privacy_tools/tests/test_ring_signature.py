from django.test import TestCase
from privacy_tools.techniques.ring_signature import RingSignature


class TestRingSignature(TestCase):
    def setUp(self):
        self.signer = RingSignature(ring_size=5)
        self.msg = b"test message for ring signature"

    def test_generate_key_pair(self):
        priv, pub = self.signer.generate_key_pair()
        self.assertIsNotNone(priv)
        self.assertIsNotNone(pub)

    def test_generate_ring_size(self):
        priv, pub = self.signer.generate_key_pair()
        ring = self.signer.generate_ring(pub, num_decoys=4)
        self.assertEqual(len(ring), 5)

    def test_sign_verify_valid(self):
        priv, pub = self.signer.generate_key_pair()
        ring = self.signer.generate_ring(pub, num_decoys=4)
        sig = self.signer.sign(self.msg, priv, ring)
        result = self.signer.verify(self.msg, sig, ring)
        self.assertTrue(result)

    def test_sign_fails_without_key_in_ring(self):
        priv, pub = self.signer.generate_key_pair()
        other_priv, other_pub = self.signer.generate_key_pair()
        ring = self.signer.generate_ring(other_pub, num_decoys=4)
        with self.assertRaises(ValueError):
            self.signer.sign(self.msg, priv, ring)

    def test_verify_rejects_tampered_message(self):
        priv, pub = self.signer.generate_key_pair()
        ring = self.signer.generate_ring(pub, num_decoys=4)
        sig = self.signer.sign(self.msg, priv, ring)
        result = self.signer.verify(b"tampered message", sig, ring)
        self.assertFalse(result)

    def test_verify_rejects_tampered_signature(self):
        priv, pub = self.signer.generate_key_pair()
        ring = self.signer.generate_ring(pub, num_decoys=4)
        sig = self.signer.sign(self.msg, priv, ring)
        sig['c0'] = sig['c0'] ^ 1
        result = self.signer.verify(self.msg, sig, ring)
        self.assertFalse(result)

    def test_evaluate_privacy_scales_with_ring_size(self):
        result_small = self.signer.evaluate_privacy(ring_size=5, num_transactions=10)
        result_large = self.signer.evaluate_privacy(ring_size=50, num_transactions=10)
        self.assertGreater(result_large['privacy_score'], result_small['privacy_score'])

    def test_evaluate_privacy_unlinkability_formula(self):
        result = self.signer.evaluate_privacy(ring_size=10, num_transactions=10)
        expected_unlinkability = 1.0 - (1.0 / 10)
        self.assertAlmostEqual(result['unlinkability_score'], expected_unlinkability, places=4)
