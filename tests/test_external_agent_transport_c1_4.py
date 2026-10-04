import unittest

from application.external_agent_transport import (
    ExternalAgentTransportState,
    ExternalAgentTransportUnavailableError,
    UnavailableExternalAgentTransport,
)


class ExternalAgentTransportC14Tests(unittest.TestCase):
    def test_unconfigured_transport_is_explicitly_unavailable(self):
        transport = UnavailableExternalAgentTransport()

        status = transport.status()

        self.assertIs(
            status.state,
            ExternalAgentTransportState.UNAVAILABLE,
        )
        self.assertFalse(status.available)
        self.assertEqual(status.provider, "UNCONFIGURED")

    def test_connect_does_not_fake_success(self):
        transport = UnavailableExternalAgentTransport()

        status = transport.connect()

        self.assertIs(
            status.state,
            ExternalAgentTransportState.UNAVAILABLE,
        )
        self.assertFalse(status.available)

    def test_send_requires_real_transport(self):
        transport = UnavailableExternalAgentTransport()

        with self.assertRaises(ExternalAgentTransportUnavailableError):
            transport.send("hello")

    def test_disconnect_reports_disconnected(self):
        transport = UnavailableExternalAgentTransport()

        status = transport.disconnect()

        self.assertIs(
            status.state,
            ExternalAgentTransportState.DISCONNECTED,
        )
        self.assertFalse(status.available)


if __name__ == "__main__":
    unittest.main()
