from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class VSCodeWorkspace:
    root: str | None


@dataclass(frozen=True)
class VSCodeBridgeResponse:
    command: str
    task_id: str
    workflow_id: str | None
    payload: str
    value: str


class VSCodeIntegration:
    """Application-facing adapter for the VS Code integration boundary."""

    def __init__(
        self,
        *,
        endpoint: str,
        timeout: float = 3.0,
    ) -> None:
        if not endpoint.strip():
            raise ValueError("endpoint must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self._endpoint = endpoint.rstrip("/")
        self._timeout = timeout
        self._workspace = VSCodeWorkspace(root=None)

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def workspace(self) -> VSCodeWorkspace:
        return self._workspace

    def workspace_opened(self, root: str | None) -> VSCodeWorkspace:
        self._workspace = VSCodeWorkspace(root=root)
        return self._workspace

    def workspace_closed(self) -> VSCodeWorkspace:
        self._workspace = VSCodeWorkspace(root=None)
        return self._workspace

    def send(
        self,
        *,
        command: str,
        task_id: str,
        payload: str,
        workflow_id: str | None = None,
        operations: tuple[dict[str, str], ...] = (),
    ) -> VSCodeBridgeResponse:
        if not command.strip():
            raise ValueError("command must not be empty")
        if not task_id.strip():
            raise ValueError("task_id must not be empty")

        body = {
            "command": command,
            "task_id": task_id,
            "payload": payload,
            "workflow_id": workflow_id,
            "operations": list(operations),
        }

        request = Request(
            self._endpoint,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        try:
            with urlopen(request, timeout=self._timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"VS Code bridge request failed: {exc}") from exc

        if "error" in result:
            raise RuntimeError(str(result["error"]))

        return VSCodeBridgeResponse(
            command=result["command"],
            task_id=result["task_id"],
            workflow_id=result.get("workflow_id"),
            payload=result["payload"],
            value=result["value"],
        )


__all__ = [
    "VSCodeBridgeResponse",
    "VSCodeIntegration",
    "VSCodeWorkspace",
]
