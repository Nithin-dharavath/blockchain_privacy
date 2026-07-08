from django.test import TestCase
from privacy_tools.techniques.crypto_mixer import CryptocurrencyMixer


class TestCryptocurrencyMixer(TestCase):
    def setUp(self):
        self.mixer = CryptocurrencyMixer(pool_size=10, min_delay=1, max_delay=10)

    def test_generate_address_format(self):
        address = self.mixer.generate_address()
        self.assertEqual(len(address), 40)
        self.assertIsInstance(address, str)

    def test_create_deposit(self):
        deposit_id = self.mixer.create_deposit(
            sender_address="alice",
            amount=100.0,
            recipient_address="bob"
        )
        self.assertIsNotNone(deposit_id)
        self.assertEqual(len(self.mixer.mixing_pool), 1)

    def test_mix_transactions_success(self):
        for i in range(5):
            self.mixer.create_deposit(
                sender_address=f"sender_{i}",
                amount=50.0 + i,
                recipient_address=f"recip_{i}"
            )
        result = self.mixer.mix_transactions()
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['num_mixed'], 0)

    def test_mix_fails_below_min_pool(self):
        self.mixer.create_deposit("alice", 100, "bob")
        self.mixer.create_deposit("charlie", 50, "dave")
        result = self.mixer.mix_transactions()
        self.assertEqual(result['status'], 'insufficient_pool')

    def test_withdraw_success(self):
        self.mixer.create_deposit("alice", 100, "bob")
        for i in range(4):
            self.mixer.create_deposit(f"sender_{i}", 50, f"recip_{i}")
        self.mixer.mix_transactions()
        deposit_id = self.mixer.mixing_pool[0]['deposit_id']
        import hashlib
        code = hashlib.sha256(deposit_id.encode()).hexdigest()[:16]
        result = self.mixer.withdraw(deposit_id, code)
        self.assertEqual(result['status'], 'success')

    def test_withdraw_invalid_code(self):
        self.mixer.create_deposit("alice", 100, "bob")
        for i in range(4):
            self.mixer.create_deposit(f"sender_{i}", 50, f"recip_{i}")
        self.mixer.mix_transactions()
        deposit_id = self.mixer.mixing_pool[0]['deposit_id']
        result = self.mixer.withdraw(deposit_id, "wrong_code")
        self.assertEqual(result['status'], 'error')

    def test_withdraw_unmixed_deposit(self):
        deposit_id = self.mixer.create_deposit("alice", 100, "bob")
        result = self.mixer.withdraw(deposit_id, "any_code")
        self.assertEqual(result['status'], 'error')
        self.assertIn('not yet mixed', result['message'])

    def test_analyze_anonymity(self):
        for i in range(5):
            self.mixer.create_deposit(f"sender_{i}", 50, f"recip_{i}")
        self.mixer.mix_transactions()
        result = self.mixer.analyze_anonymity()
        self.assertIn('anonymity_set_size', result)
        self.assertIn('privacy_score', result)
        self.assertGreater(result['anonymity_set_size'], 0)

    def test_evaluate_privacy(self):
        for i in range(5):
            self.mixer.create_deposit(f"sender_{i}", 50, f"recip_{i}")
        self.mixer.mix_transactions()
        result = self.mixer.evaluate_privacy(num_transactions=5, pool_size=10)
        self.assertIn('privacy_score', result)
        self.assertEqual(result['technique'], 'Cryptocurrency Mixer')
