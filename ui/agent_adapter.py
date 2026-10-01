"""Adapters from Agent execution models to immutable UI presentation state."""

from typing import Mapping

from application.models import ApplicationExecutionModel, PlanModel
from ui.agent_state import (
    AgentExecutionState,
    AgentHistoryEntry,
    AgentHistoryState,
    AgentInteractionState,
    AgentPlanState,
    AgentResultState,
    AgentRiskApprovalState,
    AgentRiskApprovalStepState,
    AgentTaskState,
    AgentUnderstandingState,
)


class AgentUIAdapter:
    """Convert real Agent execution data into immutable UI state."""

    @staticmethod
    def from_execution(execution) -> AgentInteractionState:
        if execution is None:
            return AgentInteractionState()

        task_description = getattr(
            execution.task,
            "description",
            "No task selected",
        )

        task = AgentTaskState(
            title=getattr(
                execution.task,
                "title",
                task_description,
            ),
            description=task_description,
            status=getattr(execution.task, "status", "No task"),
        )

        understanding = AgentUIAdapter._understanding_state(
            getattr(execution, "context_understanding", None)
        )

        plan_object = getattr(execution, "plan", None)

        plan = AgentPlanState(
            summary=getattr(
                plan_object,
                "summary",
                "No plan available",
            ),
            status=getattr(
                plan_object,
                "status",
                "No plan",
            ),
            steps=tuple(
                str(getattr(step, "operation", step))
                for step in getattr(plan_object, "steps", ())
            ),
        )

        risk_approval = AgentUIAdapter._risk_approval_state(
            plan_object
        )

        result_object = getattr(execution, "result", None)

        result = AgentResultState(
            summary=getattr(
                result_object,
                "summary",
                "No result available",
            ),
            status=AgentUIAdapter._enum_text(
                getattr(result_object, "status", "No result")
            ),
        )

        execution_state = AgentUIAdapter._execution_state(
            execution
        )

        return AgentInteractionState(
            task=task,
            understanding=understanding,
            plan=plan,
            risk_approval=risk_approval,
            execution=execution_state,
            result=result,
        )

    @staticmethod
    def history_entry(
        execution: ApplicationExecutionModel,
    ) -> AgentHistoryEntry:
        """Create a history entry directly from a real execution record."""

        if not isinstance(execution, ApplicationExecutionModel):
            raise TypeError(
                "history_entry requires ApplicationExecutionModel"
            )

        return AgentHistoryEntry(
            task=execution.task,
            plan=execution.plan,
            run=execution.run,
            result=execution.result,
            snapshot=execution.snapshot,
        )

    @staticmethod
    def history_state(
        entries,
        selected_run_id=None,
    ) -> AgentHistoryState:
        entries = tuple(entries)

        if not entries:
            return AgentHistoryState(
                entries=(),
                selected_run_id=None,
                status="Empty",
            )

        selected = selected_run_id

        if selected is None:
            selected = entries[-1].run_id

        if selected not in {entry.run_id for entry in entries}:
            selected = entries[-1].run_id

        selected_entry = next(
            entry
            for entry in entries
            if entry.run_id == selected
        )

        status = (
            "Failure"
            if str(selected_entry.result.status).upper() == "FAILED"
            else "History"
        )

        return AgentHistoryState(
            entries=entries,
            selected_run_id=selected,
            status=status,
        )

    @staticmethod
    def from_history_entry(
        entry: AgentHistoryEntry,
    ) -> AgentInteractionState:
        """Project one historical execution into the existing UI state."""

        task_description = getattr(
            entry.task,
            "description",
            "No task selected",
        )

        task = AgentTaskState(
            title=task_description,
            description=task_description,
            status="Historical",
        )

        plan_steps = tuple(
            str(getattr(step, "operation", step))
            for step in entry.plan.steps
        )

        plan = AgentPlanState(
            summary=f"{len(plan_steps)} steps",
            status="Historical",
            steps=plan_steps,
        )

        execution = AgentUIAdapter._execution_state_from_snapshot(
            entry.snapshot,
            entry.result,
        )

        result_status = AgentUIAdapter._enum_text(
            entry.result.status
        )

        result = AgentResultState(
            summary=result_status,
            status=result_status,
        )

        return AgentInteractionState(
            task=task,
            plan=plan,
            execution=execution,
            result=result,
        )

    @staticmethod
    def _execution_state_from_snapshot(snapshot, result):
        raw_step_states = getattr(snapshot, "step_states", {})

        if not isinstance(raw_step_states, Mapping):
            raw_step_states = {}

        step_states = tuple(
            f"{step_id}: {AgentUIAdapter._enum_text(status)}"
            for step_id, status in raw_step_states.items()
        )

        total_steps = len(raw_step_states)

        completed_steps = sum(
            1
            for status in raw_step_states.values()
            if AgentUIAdapter._enum_text(status)
            in {"SUCCESS", "FAILED", "SKIPPED"}
        )

        progress = (
            0
            if total_steps == 0
            else int((completed_steps / total_steps) * 100)
        )

        return AgentExecutionState(
            status=AgentUIAdapter._enum_text(
                getattr(snapshot, "run_status", "Idle")
            ),
            run_id=str(getattr(snapshot, "run_id", "")),
            current_step=getattr(snapshot, "current_step", None),
            step_states=step_states,
            progress=progress,
            failure_reason=AgentUIAdapter._failure_reason_from_record(
                result,
                raw_step_states,
            ),
            started_at=AgentUIAdapter._format_time(
                getattr(snapshot, "started_at", None)
            ),
            finished_at=AgentUIAdapter._format_time(
                getattr(snapshot, "finished_at", None)
            ),
        )

    @staticmethod
    def _failure_reason_from_record(result, step_states) -> str:
        failed_steps = tuple(
            step_id
            for step_id, status in step_states.items()
            if AgentUIAdapter._enum_text(status) == "FAILED"
        )

        if failed_steps:
            return "Failed step(s): " + ", ".join(
                str(step_id)
                for step_id in failed_steps
            )

        failure_index = getattr(result, "failure_index", None)

        if failure_index is not None:
            return f"Failure index: {failure_index}"

        return ""

    @staticmethod
    def _execution_state(execution) -> AgentExecutionState:
        snapshot = getattr(execution, "snapshot", None)

        if snapshot is None:
            result = getattr(execution, "result", None)

            return AgentExecutionState(
                status=AgentUIAdapter._enum_text(
                    getattr(result, "status", "Idle")
                )
            )

        raw_step_states = getattr(
            snapshot,
            "step_states",
            {},
        )

        if not isinstance(raw_step_states, Mapping):
            raw_step_states = {}

        step_states = tuple(
            f"{step_id}: {AgentUIAdapter._enum_text(status)}"
            for step_id, status in raw_step_states.items()
        )

        total_steps = len(raw_step_states)

        completed_steps = sum(
            1
            for status in raw_step_states.values()
            if AgentUIAdapter._enum_text(status)
            in {"SUCCESS", "FAILED", "SKIPPED"}
        )

        progress = (
            0
            if total_steps == 0
            else int((completed_steps / total_steps) * 100)
        )

        run_status = AgentUIAdapter._enum_text(
            getattr(snapshot, "run_status", "Idle")
        )

        return AgentExecutionState(
            status=run_status,
            run_id=str(getattr(snapshot, "run_id", "")),
            current_step=getattr(snapshot, "current_step", None),
            step_states=step_states,
            progress=progress,
            failure_reason=AgentUIAdapter._failure_reason(
                execution,
                raw_step_states,
            ),
            started_at=AgentUIAdapter._format_time(
                getattr(snapshot, "started_at", None)
            ),
            finished_at=AgentUIAdapter._format_time(
                getattr(snapshot, "finished_at", None)
            ),
        )

    @staticmethod
    def _failure_reason(execution, step_states) -> str:
        failed_steps = tuple(
            step_id
            for step_id, status in step_states.items()
            if AgentUIAdapter._enum_text(status) == "FAILED"
        )

        if failed_steps:
            return "Failed step(s): " + ", ".join(
                str(step_id)
                for step_id in failed_steps
            )

        result = getattr(execution, "result", None)

        explicit_reason = getattr(
            result,
            "failure_reason",
            "",
        )

        if explicit_reason:
            return str(explicit_reason)

        return ""

    @staticmethod
    def _format_time(value) -> str:
        if value is None:
            return ""

        return value.isoformat()

    @staticmethod
    def _enum_text(value) -> str:
        return str(getattr(value, "value", value))

    @staticmethod
    def _understanding_state(
        result,
    ) -> AgentUnderstandingState:
        if result is None:
            return AgentUnderstandingState()

        summary = getattr(result, "summary", "")

        if not summary:
            summary = "Understanding available"

        return AgentUnderstandingState(
            summary=summary,
            relevant_files=tuple(
                str(path)
                for path in getattr(result, "relevant_files", ())
            ),
            relevant_symbols=tuple(
                str(symbol)
                for symbol in getattr(result, "relevant_symbols", ())
            ),
            relationships=tuple(
                str(relationship)
                for relationship in getattr(result, "relationships", ())
            ),
            dependencies=tuple(
                str(dependency)
                for dependency in getattr(result, "dependencies", ())
            ),
        )

    @staticmethod
    def _risk_approval_state(plan) -> AgentRiskApprovalState:
        if not isinstance(plan, PlanModel):
            return AgentRiskApprovalState()

        presentation_steps = tuple(
            AgentRiskApprovalStepState(
                step_id=step.step_id,
                risk=step.risk,
                approval=step.approval,
                readiness=step.readiness,
                reason=step.reason,
                ready=step.ready,
            )
            for step in plan.steps
        )

        return AgentRiskApprovalState(
            ready=plan.ready,
            steps=presentation_steps,
            issues=plan.issues,
            warnings=plan.warnings,
        )


__all__ = ["AgentUIAdapter"]
