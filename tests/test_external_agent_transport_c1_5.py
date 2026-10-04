import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from application.local_http_external_agent_transport import (
    LocalHTTPExternalAgentTransport,
)
from application.external_agent_transport import ExternalAgentTransportState


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        response = json.dumps({"message": "echo:" + body["message"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        pass


class TestLocalHTTPExternalAgentTransportC15(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()
        self.endpoint = f"http://127.0.0.1:{self.server.server_port}/"
        self.transport = LocalHTTPExternalAgentTransport(self.endpoint)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_connect_requires_real_http_endpoint(self):
        status = self.transport.connect()

        self.assertIs(status.state, ExternalAgentTransportState.CONNECTED)
        self.assertTrue(status.available)

    def test_send_uses_real_http_request(self):
        self.transport.connect()

        result = self.transport.send("hello")

        self.assertEqual(result, "echo:hello")

    def test_disconnect_reports_disconnected(self):
        self.transport.connect()

        status = self.transport.disconnect()

        self.assertIs(status.state, ExternalAgentTransportState.DISCONNECTED)
        self.assertFalse(status.available)

    def test_connection_loss_is_not_reported_as_success(self):
        self.transport.connect()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

        with self.assertRaises(RuntimeError):
            self.transport.send("hello")

        self.assertIs(
            self.transport.status().state,
            ExternalAgentTransportState.DISCONNECTED,
        )


if __name__ == "__main__":
    unittest.main()
