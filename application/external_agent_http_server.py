from __future__ import annotations

import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from application.external_agent import ExternalAgentRequest
from application.external_agent_bridge import (
    ExternalAgentCommand,
    ExternalAgentMessageBridge,
)
from application.universal_agent_interface import AgentOperationRequest


class ExternalAgentHTTPServer:
    """Real localhost HTTP adapter for ExternalAgentMessageBridge."""

    def __init__(
        self,
        bridge: ExternalAgentMessageBridge,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        if not isinstance(bridge, ExternalAgentMessageBridge):
            raise TypeError("bridge must be an ExternalAgentMessageBridge")

        self._bridge = bridge
        self._server = ThreadingHTTPServer(
            (host, port),
            self._make_handler(),
        )
        self._thread: Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        return self._server.server_address

    @property
    def url(self) -> str:
        host, port = self.address
        return f"http://{host}:{port}/agent"

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = Thread(
            target=self._server.serve_forever,
            daemon=True,
        )
        self._thread.start()

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._thread = None

    def _make_handler(self):
        bridge = self._bridge

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                if self.path != "/agent":
                    self.send_error(404)
                    return

                try:
                    length = int(self.headers["Content-Length"])
                    body = json.loads(self.rfile.read(length).decode("utf-8"))

                    request = ExternalAgentRequest(
                        task_id=body["task_id"],
                        payload=body["payload"],
                        workflow_id=body.get("workflow_id"),
                    )
                    command = ExternalAgentCommand(body["command"])

                    operations = tuple(
                        AgentOperationRequest(item["name"])
                        for item in body.get("operations", [])
                    )

                    result = bridge.dispatch(
                        request,
                        command,
                        operations=operations,
                    )

                    response = {
                        "command": result.command.value,
                        "task_id": result.response.task_id,
                        "workflow_id": result.response.workflow_id,
                        "payload": result.response.payload,
                        "value": repr(result.value),
                    }

                    encoded = json.dumps(response).encode("utf-8")
                    self.send_response(200)
                    self.send_header(
                        "Content-Type",
                        "application/json",
                    )
                    self.send_header(
                        "Content-Length",
                        str(len(encoded)),
                    )
                    self.end_headers()
                    self.wfile.write(encoded)

                except (KeyError, ValueError, TypeError, RuntimeError) as exc:
                    encoded = json.dumps(
                        {"error": str(exc)}
                    ).encode("utf-8")
                    self.send_response(400)
                    self.send_header(
                        "Content-Type",
                        "application/json",
                    )
                    self.send_header(
                        "Content-Length",
                        str(len(encoded)),
                    )
                    self.end_headers()
                    self.wfile.write(encoded)

            def log_message(self, format, *args):
                pass

        return Handler


__all__ = ["ExternalAgentHTTPServer"]
