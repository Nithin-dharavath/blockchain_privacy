import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from django.test import TestCase
from experiments.experiment_runner import PrivacyExperimentRunner


class TestPrivacyExperimentRunner(TestCase):
    def setUp(self):
        self.technique = MagicMock()
        self.technique.technique_type = 'ring_signature'
        self.technique.security_level = 5
        self.experiment = MagicMock()
        self.experiment.privacy_technique = self.technique
        self.experiment.configuration = {'ring_size': 5, 'num_transactions': 10}
        self.df = pd.DataFrame({'col1': range(20), 'col2': range(20, 40)})
        self.runner = PrivacyExperimentRunner(self.experiment, self.df)

    def test_unknown_technique_raises(self):
        tech = MagicMock()
        tech.technique_type = 'unknown_type'
        exp = MagicMock()
        exp.privacy_technique = tech
        exp.configuration = {}
        runner = PrivacyExperimentRunner(exp, self.df)
        with self.assertRaises(ValueError):
            runner.run()

    def test_ensure_accuracy_zero_total(self):
        result = self.runner._ensure_accuracy(0, 0)
        self.assertIsNone(result)

    @patch('experiments.experiment_runner.random.uniform', return_value=0.0)
    def test_ensure_accuracy_clamps_range(self, mock_uniform):
        result = self.runner._ensure_accuracy(5, 10)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_get_fallback_accuracy_all_techniques(self):
        technique_types = ['ring_signature', 'zkp', 'smpc', 'tee', 'mixer']
        for t in technique_types:
            tech = MagicMock()
            tech.technique_type = t
            exp = MagicMock()
            exp.privacy_technique = tech
            exp.configuration = {}
            runner = PrivacyExperimentRunner(exp, self.df)
            fallback = runner._get_fallback_accuracy()
            self.assertIsInstance(fallback, float)
            self.assertGreater(fallback, 0)
            self.assertLessEqual(fallback, 1.0)

    def test_calculate_privacy_score_basic(self):
        score = self.runner._calculate_privacy_score(50, {})
        self.assertIsInstance(score, (int, float))

    def test_calculate_privacy_score_with_all_factors(self):
        factors = {
            'anonymity_set': 10,
            'success_rate': 0.95,
            'unlinkability': 0.8,
            'collusion_resistance': 0.7,
            'security_bits': 256,
        }
        score = self.runner._calculate_privacy_score(50, factors)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_calculate_privacy_score_security_level_mapping(self):
        tech_low = MagicMock()
        tech_low.security_level = 2
        exp_low = MagicMock()
        exp_low.privacy_technique = tech_low
        exp_low.configuration = {}
        runner_low = PrivacyExperimentRunner(exp_low, self.df)

        tech_high = MagicMock()
        tech_high.security_level = 9
        exp_high = MagicMock()
        exp_high.privacy_technique = tech_high
        exp_high.configuration = {}
        runner_high = PrivacyExperimentRunner(exp_high, self.df)

        score_low = runner_low._calculate_privacy_score(50, {})
        score_high = runner_high._calculate_privacy_score(50, {})
        self.assertGreaterEqual(score_high, score_low)

    def test_calculate_privacy_score_respects_cap(self):
        score = self.runner._calculate_privacy_score(
            200,
            {'anonymity_set': 1000, 'success_rate': 1.0}
        )
        self.assertLessEqual(score, 100)


class TestRunnerRingSignature(TestCase):
    def setUp(self):
        self.technique = MagicMock()
        self.technique.technique_type = 'ring_signature'
        self.technique.security_level = 5
        self.experiment = MagicMock()
        self.experiment.privacy_technique = self.technique
        self.experiment.configuration = {'ring_size': 5, 'num_transactions': 5}
        self.df = pd.DataFrame({'col1': range(10), 'col2': range(10, 20)})

    @patch('experiments.experiment_runner.rsa.generate_private_key')
    def test_run_returns_all_keys(self, mock_gen_key):
        mock_private = MagicMock()
        mock_public = MagicMock()
        mock_gen_key.return_value = mock_private
        mock_private.public_key.return_value = mock_public

        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_ring_signature()
        expected_keys = [
            'privacy_score', 'execution_time', 'accuracy',
            'throughput', 'anonymity_set_size', 'metrics',
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        self.assertIn('ring_size', result['metrics'])
        self.assertIn('total_operations', result['metrics'])

    @patch('experiments.experiment_runner.rsa.generate_private_key')
    def test_run_with_empty_df(self, mock_gen_key):
        empty_df = pd.DataFrame()
        exp = MagicMock()
        exp.privacy_technique = self.technique
        exp.configuration = {'ring_size': 3, 'num_transactions': 100}
        runner = PrivacyExperimentRunner(exp, empty_df)
        result = runner._run_ring_signature()
        self.assertIn('privacy_score', result)

    @patch('experiments.experiment_runner.rsa.generate_private_key')
    def test_fallback_implementation(self, mock_gen_key):
        mock_gen_key.side_effect = Exception("RSA failure")
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_ring_signature()
        self.assertIn('metrics', result)
        self.assertEqual(result['metrics']['signature_scheme'], 'Hash-based-Ring')


class TestRunnerZKP(TestCase):
    def setUp(self):
        self.technique = MagicMock()
        self.technique.technique_type = 'zkp'
        self.technique.security_level = 7
        self.experiment = MagicMock()
        self.experiment.privacy_technique = self.technique
        self.experiment.configuration = {'num_proofs': 5}
        self.df = pd.DataFrame({'col1': range(10), 'col2': range(10, 20)})

    def test_run_returns_all_keys(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_zkp()
        expected_keys = [
            'privacy_score', 'execution_time', 'accuracy',
            'throughput', 'anonymity_set_size', 'metrics',
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        self.assertIn('zero_knowledge_property', result['metrics'])
        self.assertTrue(result['metrics']['zero_knowledge_property'])

    def test_run_real_proof_verification(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_zkp()
        self.assertGreater(result['metrics']['successful_operations'], 0)


class TestRunnerSMPC(TestCase):
    def setUp(self):
        self.technique = MagicMock()
        self.technique.technique_type = 'smpc'
        self.technique.security_level = 6
        self.experiment = MagicMock()
        self.experiment.privacy_technique = self.technique
        self.experiment.configuration = {
            'num_parties': 3, 'threshold': 2, 'num_computations': 5,
        }
        self.df = pd.DataFrame({'col1': range(10), 'col2': range(10, 20)})

    def test_run_returns_all_keys(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_smpc()
        expected_keys = [
            'privacy_score', 'execution_time', 'accuracy',
            'throughput', 'anonymity_set_size', 'metrics',
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        self.assertIn('num_parties', result['metrics'])

    def test_run_shamir_reconstruction(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_smpc()
        self.assertGreater(result['metrics']['successful_operations'], 0)


class TestRunnerTEE(TestCase):
    def setUp(self):
        self.technique = MagicMock()
        self.technique.technique_type = 'tee'
        self.technique.security_level = 7
        self.experiment = MagicMock()
        self.experiment.privacy_technique = self.technique
        self.experiment.configuration = {'num_operations': 3, 'data_size_mb': 1}
        self.df = pd.DataFrame({'col1': range(10), 'col2': range(10, 20)})

    def test_run_returns_all_keys(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_tee()
        expected_keys = [
            'privacy_score', 'execution_time', 'accuracy',
            'throughput', 'anonymity_set_size', 'metrics',
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        self.assertIn('encryption_algorithm', result['metrics'])

    def test_run_aes_roundtrip(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_tee()
        self.assertGreater(result['metrics']['successful_operations'], 0)


class TestRunnerMixer(TestCase):
    def setUp(self):
        self.technique = MagicMock()
        self.technique.technique_type = 'mixer'
        self.technique.security_level = 4
        self.experiment = MagicMock()
        self.experiment.privacy_technique = self.technique
        self.experiment.configuration = {'pool_size': 5, 'num_transactions': 8}
        self.df = pd.DataFrame({'col1': range(20), 'col2': range(20, 40)})

    def test_run_returns_all_keys(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_mixer()
        expected_keys = [
            'privacy_score', 'execution_time', 'accuracy',
            'throughput', 'anonymity_set_size', 'metrics',
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        self.assertIn('pool_size', result['metrics'])

    def test_run_mixing_logic(self):
        runner = PrivacyExperimentRunner(self.experiment, self.df)
        result = runner._run_mixer()
        self.assertGreater(result['metrics']['successful_operations'], 0)
