from __future__ import annotations

import unittest

from application.external_agent_api_state import (
    ExternalAPIState,
    ExternalAPIStateDetector,
)


class ExternalAPIStateC58Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = ExternalAPIStateDetector()

    def test_connected(self):
        self.assertEqual(
            self.detector.detect("Connected").state,
            ExternalAPIState.CONNECTED,
        )

    def test_disconnected(self):
        self.assertEqual(
            self.detector.detect("Disconnected").state,
            ExternalAPIState.DISCONNECTED,
        )

    def test_rate_limited(self):
        self.assertEqual(
            self.detector.detect("Rate Limited").state,
            ExternalAPIState.RATE_LIMITED,
        )

    def test_quota(self):
        self.assertEqual(
            self.detector.detect("Quota").state,
            ExternalAPIState.QUOTA,
        )

    def test_error(self):
        self.assertEqual(
            self.detector.detect("Error").state,
            ExternalAPIState.ERROR,
        )

    def test_unavailable(self):
        self.assertEqual(
            self.detector.detect("Unavailable").state,
            ExternalAPIState.UNAVAILABLE,
        )

    def test_message_is_preserved(self):
        result = self.detector.detect(
            "Error",
            message="formal API returned an error",
        )
        self.assertEqual(result.message, "formal API returned an error")


class ExternalAPIStateC59Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = ExternalAPIStateDetector()

    def test_missing_state_becomes_unknown(self):
        result = self.detector.detect(None)
        self.assertEqual(result.state, ExternalAPIState.UNKNOWN)

    def test_empty_state_becomes_unknown(self):
        result = self.detector.detect("")
        self.assertEqual(result.state, ExternalAPIState.UNKNOWN)

    def test_unsupported_state_becomes_unknown(self):
        result = self.detector.detect("Something Else")
        self.assertEqual(result.state, ExternalAPIState.UNKNOWN)

    def test_unknown_does_not_guess_connected(self):
        result = self.detector.detect("Something Else")
        self.assertNotEqual(result.state, ExternalAPIState.CONNECTED)

    def test_unknown_does_not_guess_error(self):
        result = self.detector.detect("Something Else")
        self.assertNotEqual(result.state, ExternalAPIState.ERROR)

    def test_unknown_preserves_explicit_message(self):
        result = self.detector.detect(
            "Something Else",
            message="provider returned an unsupported state",
        )
        self.assertEqual(
            result.state,
            ExternalAPIState.UNKNOWN,
        )
        self.assertEqual(
            result.message,
            "provider returned an unsupported state",
        )

    def test_invalid_state_type_is_rejected(self):
        with self.assertRaises(TypeError):
            self.detector.detect(123)


if __name__ == "__main__":
    unittest.main()
