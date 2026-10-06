"""Checkpoint progression for execution contexts."""
from dataclasses import replace
from datetime import datetime, timezone

from application.execution_context import ExecutionContext


CHECKPOINT_EVENTS = frozenset(
    {
        "EXECUTION_STARTED",
        "STEP_STARTED",
        "STEP_COMPLETED",
        "PROCESS_STARTED",
        "PROCESS_EXITED",
        "TERMINAL_CONNECTED",
        "TERMINAL_DISCONNECTED",
        "WAITING_FOR_USER",
        "WAITING_EXTERNAL",
        "EXECUTION_PAUSED",
        "EXECUTION_RESUMED",
        "EXECUTION_FAILED",
        "EXECUTION_BLOCKED",
        "EXECUTION_COMPLETED",
    }
)


def checkpoint(
    context: ExecutionContext,
    event: str,
) -> ExecutionContext:
    if not isinstance(context, ExecutionContext):
        raise TypeError("context must be an ExecutionContext")

    if not isinstance(event, str) or not event.strip():
        raise ValueError("event must not be empty")

    if event not in CHECKPOINT_EVENTS:
        raise ValueError(f"unsupported checkpoint event: {event}")

    return replace(
        context,
        checkpoint_sequence=context.checkpoint_sequence + 1,
        checkpointed_at=datetime.now(timezone.utc),
    )


def checkpoint_if_needed(
    context: ExecutionContext,
    event: str,
) -> ExecutionContext:
    if event not in CHECKPOINT_EVENTS:
        return context

    return checkpoint(context, event)
