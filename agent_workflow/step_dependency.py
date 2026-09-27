"""Deterministic read-only workflow step dependency analysis."""

from dataclasses import dataclass
from typing import Mapping

from agent_workflow.workflow_plan import WorkflowPlan


@dataclass(frozen=True)
class StepDependencyResult:
    """Immutable dependency analysis result."""

    dependencies: tuple[tuple[str, tuple[str, ...]], ...]
    issues: tuple[str, ...]
    execution_order: tuple[str, ...]


class StepDependencyAwareness:
    """Analyze explicit workflow step dependencies without execution."""

    def analyze(
        self,
        plan: WorkflowPlan,
        dependencies: Mapping[str, tuple[str, ...]] | None = None,
    ) -> StepDependencyResult:
        if not isinstance(plan, WorkflowPlan):
            raise TypeError("plan must be a WorkflowPlan")

        step_ids = tuple(step.step_id for step in plan.steps)
        step_set = set(step_ids)
        issues: list[str] = []

        if len(step_ids) != len(step_set):
            seen: set[str] = set()
            for step_id in step_ids:
                if step_id in seen:
                    issues.append(
                        f"{step_id}: duplicate step_id"
                    )
                seen.add(step_id)

        for step_id in step_ids:
            if not step_id:
                issues.append("step_id must not be empty")

        raw_dependencies = dependencies or {}

        for step_id in raw_dependencies:
            if step_id not in step_set:
                issues.append(
                    f"{step_id}: dependency target is unknown"
                )

        normalized: dict[str, tuple[str, ...]] = {}

        for step_id in step_ids:
            refs = tuple(raw_dependencies.get(step_id, ()))

            if len(refs) != len(set(refs)):
                issues.append(
                    f"{step_id}: duplicate dependency"
                )

            for dependency_id in refs:
                if dependency_id not in step_set:
                    issues.append(
                        f"{step_id}: unknown dependency "
                        f"{dependency_id}"
                    )
                elif dependency_id == step_id:
                    issues.append(
                        f"{step_id}: self dependency"
                    )

            normalized[step_id] = refs

        ordered_dependencies = tuple(
            (step_id, normalized[step_id])
            for step_id in step_ids
        )

        execution_order = self._topological_order(
            step_ids,
            normalized,
            issues,
        )

        return StepDependencyResult(
            dependencies=ordered_dependencies,
            issues=tuple(dict.fromkeys(issues)),
            execution_order=execution_order,
        )

    @staticmethod
    def _topological_order(
        step_ids: tuple[str, ...],
        dependencies: dict[str, tuple[str, ...]],
        issues: list[str],
    ) -> tuple[str, ...]:
        if issues:
            return step_ids

        position = {
            step_id: index
            for index, step_id in enumerate(step_ids)
        }

        remaining = {
            step_id: set(dependencies[step_id])
            for step_id in step_ids
        }

        result: list[str] = []

        while remaining:
            ready = sorted(
                (
                    step_id
                    for step_id, refs in remaining.items()
                    if not refs
                ),
                key=position.__getitem__,
            )

            if not ready:
                cycle_nodes = tuple(
                    sorted(remaining, key=position.__getitem__)
                )
                issues.append(
                    "dependency cycle detected: "
                    + " -> ".join(cycle_nodes)
                )
                return step_ids

            for step_id in ready:
                result.append(step_id)
                del remaining[step_id]

            for refs in remaining.values():
                refs.difference_update(ready)

        return tuple(result)
