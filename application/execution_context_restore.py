"""Restart-safe restoration of execution contexts."""
from dataclasses import dataclass, replace

from application.execution_context import ExecutionContext
from application.execution_context_storage import ExecutionContextStorage


@dataclass(frozen=True)
class RestoredExecutionContext:
    context: ExecutionContext
    process_revalidation_required: bool
    terminal_revalidation_required: bool


class ExecutionContextRestoreService:
    def __init__(self, storage: ExecutionContextStorage):
        self._storage = storage

    def restore(self) -> RestoredExecutionContext | None:
        context = self._storage.load()

        if context is None:
            return None

        restored = replace(
            context,
            recoverability="REVALIDATION_REQUIRED",
        )

        return RestoredExecutionContext(
            context=restored,
            process_revalidation_required=(
                restored.process_id is not None
            ),
            terminal_revalidation_required=(
                restored.terminal_id is not None
                or restored.terminal_session_id is not None
            ),
        )
