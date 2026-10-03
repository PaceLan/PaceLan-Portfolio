from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)
from application.verification import VerificationResult, VerificationStatus


class WorkflowStorage:
    """Persist one application execution bundle as JSON."""

    SCHEMA_VERSION = 1
    DIRECTORY_NAME = ".pacepilot"
    FILE_NAME = "workflow.json"

    def _storage_path(self, project_path: str | Path) -> Path:
        return Path(project_path).resolve() / self.DIRECTORY_NAME / self.FILE_NAME

    def exists(self, project_path: str | Path) -> bool:
        return self._storage_path(project_path).is_file()

    def save(
        self,
        execution: ApplicationExecutionModel,
        project_path: str | Path,
    ) -> Path:
        if not isinstance(execution, ApplicationExecutionModel):
            raise TypeError("execution must be an ApplicationExecutionModel")

        root = Path(project_path).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("project_path must be an existing directory")

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "task": self._task_to_dict(execution.task),
            "plan": self._plan_to_dict(execution.plan),
            "run": {
                "run_id": execution.run.run_id,
                "task_id": execution.run.task_id,
            },
            "result": self._result_to_dict(execution.result),
            "snapshot": self._snapshot_to_dict(execution.snapshot),
            "verification": self._verification_to_dict(execution.verification),
        }

        target = self._storage_path(root)
        target.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".workflow.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        try:
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        return target

    def load(self, project_path: str | Path) -> ApplicationExecutionModel:
        target = self._storage_path(project_path)

        if not target.is_file():
            raise FileNotFoundError(
                f"Workflow storage does not exist: {target}"
            )

        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid workflow storage: {target}") from exc

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported workflow storage schema: "
                f"{payload.get('schema_version')!r}"
            )

        try:
            return ApplicationExecutionModel(
                task=self._task_from_dict(payload["task"]),
                plan=self._plan_from_dict(payload["plan"]),
                run=self._run_from_dict(payload["run"]),
                result=self._result_from_dict(payload["result"]),
                snapshot=self._snapshot_from_dict(payload["snapshot"]),
                verification=self._verification_from_dict(
                    payload.get("verification")
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid workflow storage structure") from exc

    @staticmethod
    def _task_to_dict(task: TaskModel) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "description": task.description,
            "context": task.context,
        }

    @staticmethod
    def _task_from_dict(data: dict[str, Any]) -> TaskModel:
        return TaskModel(
            task_id=data["task_id"],
            project_id=data["project_id"],
            description=data.get("description", ""),
            context=data.get("context", ""),
        )

    @staticmethod
    def _plan_to_dict(plan: PlanModel) -> dict[str, Any]:
        return {
            "task_id": plan.task_id,
            "project_id": plan.project_id,
            "steps": [
                {
                    "step_id": step.step_id,
                    "operation": step.operation,
                    "risk": step.risk,
                    "approval": step.approval,
                    "target": step.target,
                    "context": step.context,
                    "readiness": step.readiness,
                    "reason": step.reason,
                    "ready": step.ready,
                }
                for step in plan.steps
            ],
            "ready": plan.ready,
            "issues": list(plan.issues),
            "warnings": list(plan.warnings),
        }

    @staticmethod
    def _plan_from_dict(data: dict[str, Any]) -> PlanModel:
        return PlanModel(
            task_id=data["task_id"],
            project_id=data["project_id"],
            steps=tuple(
                StepModel(
                    step_id=step["step_id"],
                    operation=step["operation"],
                    risk=step.get("risk", "SAFE"),
                    approval=step.get("approval", "NOT_REQUESTED"),
                    target=step.get("target", "."),
                    context=step.get("context"),
                    readiness=step.get("readiness", "UNKNOWN"),
                    reason=step.get("reason", ""),
                    ready=step.get("ready", False),
                )
                for step in data.get("steps", [])
            ),
            ready=data.get("ready", False),
            issues=tuple(data.get("issues", [])),
            warnings=tuple(data.get("warnings", [])),
        )

    @staticmethod
    def _run_from_dict(data: dict[str, Any]) -> RunModel:
        return RunModel(
            run_id=data["run_id"],
            task_id=data["task_id"],
        )

    @staticmethod
    def _result_to_dict(result: ResultModel) -> dict[str, Any]:
        return {
            "run_id": result.run_id,
            "status": result.status,
            "total_steps": result.total_steps,
            "successful_steps": result.successful_steps,
            "failed_steps": result.failed_steps,
            "blocked_steps": result.blocked_steps,
            "completed_successfully": result.completed_successfully,
            "failure_index": result.failure_index,
        }

    @staticmethod
    def _result_from_dict(data: dict[str, Any]) -> ResultModel:
        return ResultModel(
            run_id=data["run_id"],
            status=data["status"],
            total_steps=data.get("total_steps", 0),
            successful_steps=data.get("successful_steps", 0),
            failed_steps=data.get("failed_steps", 0),
            blocked_steps=data.get("blocked_steps", 0),
            completed_successfully=data.get("completed_successfully", False),
            failure_index=data.get("failure_index"),
        )

    @staticmethod
    def _snapshot_to_dict(snapshot: SnapshotModel) -> dict[str, Any]:
        return {
            "run_id": snapshot.run_id,
            "task_id": snapshot.task_id,
            "run_status": snapshot.run_status,
            "step_states": dict(snapshot.step_states),
            "current_step": snapshot.current_step,
            "started_at": (
                snapshot.started_at.isoformat()
                if isinstance(snapshot.started_at, datetime)
                else None
            ),
            "finished_at": (
                snapshot.finished_at.isoformat()
                if isinstance(snapshot.finished_at, datetime)
                else None
            ),
        }

    @staticmethod
    def _snapshot_from_dict(data: dict[str, Any]) -> SnapshotModel:
        started_at = data.get("started_at")
        finished_at = data.get("finished_at")

        return SnapshotModel(
            run_id=data["run_id"],
            task_id=data["task_id"],
            run_status=data["run_status"],
            step_states=dict(data.get("step_states", {})),
            current_step=data.get("current_step"),
            started_at=(
                datetime.fromisoformat(started_at)
                if started_at is not None
                else None
            ),
            finished_at=(
                datetime.fromisoformat(finished_at)
                if finished_at is not None
                else None
            ),
        )

    @staticmethod
    def _verification_to_dict(
        verification: VerificationResult | None,
    ) -> dict[str, Any] | None:
        if verification is None:
            return None

        return {
            "run_id": verification.run_id,
            "status": verification.status.value,
            "verified": verification.verified,
            "reason": verification.reason,
            "checked_steps": verification.checked_steps,
            "successful_steps": verification.successful_steps,
            "failed_steps": verification.failed_steps,
            "blocked_steps": verification.blocked_steps,
        }

    @staticmethod
    def _verification_from_dict(
        data: dict[str, Any] | None,
    ) -> VerificationResult | None:
        if data is None:
            return None

        return VerificationResult(
            run_id=data["run_id"],
            status=VerificationStatus(data["status"]),
            verified=data["verified"],
            reason=data["reason"],
            checked_steps=data["checked_steps"],
            successful_steps=data["successful_steps"],
            failed_steps=data["failed_steps"],
            blocked_steps=data["blocked_steps"],
        )


__all__ = ["WorkflowStorage"]
