import unittest

from application.external_agent_retry_policy import (
    ExternalAgentRetryDecision,
    ExternalAgentRetryPolicy,
)


class TestExternalAgentRetryPolicyC53(unittest.TestCase):
    def test_retry_is_allowed_before_limit(self):
        result = ExternalAgentRetryPolicy(max_attempts=3).decide(attempt=0)
        self.assertEqual(result.decision, ExternalAgentRetryDecision.RETRY)
        self.assertEqual(result.attempt, 0)
        self.assertEqual(result.max_attempts, 3)

    def test_retry_is_allowed_for_last_permitted_attempt(self):
        result = ExternalAgentRetryPolicy(max_attempts=3).decide(attempt=2)
        self.assertEqual(result.decision, ExternalAgentRetryDecision.RETRY)

    def test_limit_stops_retry(self):
        result = ExternalAgentRetryPolicy(max_attempts=3).decide(attempt=3)
        self.assertEqual(result.decision, ExternalAgentRetryDecision.STOP)

    def test_attempt_above_limit_stops_retry(self):
        result = ExternalAgentRetryPolicy(max_attempts=3).decide(attempt=99)
        self.assertEqual(result.decision, ExternalAgentRetryDecision.STOP)

    def test_negative_attempt_rejected(self):
        with self.assertRaises(ValueError):
            ExternalAgentRetryPolicy().decide(attempt=-1)

    def test_boolean_attempt_rejected(self):
        with self.assertRaises(TypeError):
            ExternalAgentRetryPolicy().decide(attempt=True)

    def test_invalid_max_attempts_rejected(self):
        with self.assertRaises(ValueError):
            ExternalAgentRetryPolicy(max_attempts=0)

    def test_boolean_max_attempts_rejected(self):
        with self.assertRaises(TypeError):
            ExternalAgentRetryPolicy(max_attempts=True)

    def test_retry_delay_is_reported_without_sleeping(self):
        policy = ExternalAgentRetryPolicy(
            max_attempts=3,
            retry_delay_seconds=2.5,
        )
        result = policy.decide(attempt=1)
        self.assertEqual(result.delay_seconds, 2.5)
        self.assertEqual(policy.retry_delay_seconds, 2.5)

    def test_stop_has_no_retry_delay(self):
        result = ExternalAgentRetryPolicy(
            max_attempts=1,
            retry_delay_seconds=2.5,
        ).decide(attempt=1)
        self.assertEqual(result.decision, ExternalAgentRetryDecision.STOP)
        self.assertEqual(result.delay_seconds, 0.0)

    def test_negative_retry_delay_rejected(self):
        with self.assertRaises(ValueError):
            ExternalAgentRetryPolicy(retry_delay_seconds=-1)

    def test_boolean_retry_delay_rejected(self):
        with self.assertRaises(TypeError):
            ExternalAgentRetryPolicy(retry_delay_seconds=True)

    def test_no_unbounded_retry(self):
        policy = ExternalAgentRetryPolicy(max_attempts=1)
        result = policy.decide(attempt=10_000)
        self.assertEqual(result.decision, ExternalAgentRetryDecision.STOP)


if __name__ == "__main__":
    unittest.main()
