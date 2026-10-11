from __future__ import annotations

from application.models import PlanModel, ProgressModel, SnapshotModel
from application.services import ProgressService


class AutonomousProgressService:
    """Application boundary for autonomous progress observations."""

    @staticmethod
    def from_plan(plan: PlanModel) -> ProgressModel:
        return ProgressService.from_plan(plan)

    @staticmethod
    def from_snapshot(snapshot: SnapshotModel) -> ProgressModel:
        return ProgressService.from_snapshot(snapshot)


__all__ = ["AutonomousProgressService"]
