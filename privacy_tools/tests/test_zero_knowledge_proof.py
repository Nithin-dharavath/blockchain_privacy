from django.test import TestCase
from privacy_tools.techniques.zero_knowledge_proof import ZeroKnowledgeProof


class TestZeroKnowledgeProof(TestCase):
    def setUp(self):
        self.zkp = ZeroKnowledgeProof()
        self.secret = 42
        self.statement = "I know the secret"

    def test_generate_commitment(self):
        result = self.zkp.generate_commitment(self.secret)
        self.assertIn('commitment', result)
        self.assertIn('blinding_factor', result)

    def test_generate_proof(self):
        proof = self.zkp.generate_proof(self.secret, self.statement)
        self.assertIn('commitment', proof)
        self.assertIn('challenge', proof)
        self.assertIn('response', proof)
        self.assertEqual(proof['statement'], self.statement)

    def test_verify_proof_valid(self):
        proof = self.zkp.generate_proof(self.secret, self.statement)
        result = self.zkp.verify_proof(proof)
        self.assertTrue(result)

    def test_verify_proof_invalid_tampered(self):
        proof = self.zkp.generate_proof(self.secret, self.statement)
        proof['response'] = proof['response'] ^ 1
        result = self.zkp.verify_proof(proof)
        self.assertFalse(result)

    def test_prove_range_valid(self):
        result = self.zkp.prove_range(50, 0, 100)
        self.assertIn('lower_bound_proof', result)
        self.assertIn('upper_bound_proof', result)
        self.assertEqual(result['range'], (0, 100))

    def test_prove_range_out_of_bounds_raises(self):
        with self.assertRaises(ValueError):
            self.zkp.prove_range(150, 0, 100)

    def test_evaluate_privacy(self):
        result = self.zkp.evaluate_privacy(num_proofs=10, proof_size_kb=5)
        self.assertIn('privacy_score', result)
        self.assertTrue(result['zero_knowledge_property'])
        self.assertEqual(result['technique'], 'Zero-Knowledge Proofs')
