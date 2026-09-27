"""Deterministic task-driven planner intelligence."""

from collections.abc import Iterable
from pathlib import Path

from agent_workflow.context_understanding import ContextUnderstandingResult
from agent_workflow.plan_builder import build_plan, validate_plan
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class PlannerIntelligence:
    """Create deterministic workflow plans from understood project context.

    This layer decides what should be planned from a task and its
    understood project context. It never executes workflow actions.
    """

    _INSPECT_KEYWORDS = frozenset(
        {
            "inspect",
            "check",
            "review",
            "locate",
            "find",
        }
    )

    _ANALYSIS_KEYWORDS = frozenset(
        {
            "analyze",
            "analysis",
            "understand",
            "explain",
            "investigate",
        }
    )

    _DEPENDENCY_KEYWORDS = frozenset(
        {
            "dependency",
            "dependencies",
            "depend",
            "import",
            "imports",
            "imported",
            "upstream",
            "downstream",
            "chain",
        }
    )

    def plan(
        self,
        task: WorkflowTask,
        context: ContextUnderstandingResult,
        actions: Iterable[WorkflowStep] = (),
    ) -> WorkflowPlan:
        if not isinstance(task, WorkflowTask):
            raise TypeError("task must be a WorkflowTask")

        if not isinstance(
            context,
            ContextUnderstandingResult,
        ):
            raise TypeError(
                "context must be a ContextUnderstandingResult"
            )

        steps = tuple(actions)

        if steps:
            planned_steps = self._inject_context(
                steps,
                context,
            )
        else:
            planned_steps = self._generate_steps(
                task,
                context,
            )

        plan = build_plan(
            task,
            planned_steps,
        )

        return validate_plan(plan)

    @classmethod
    def _generate_steps(
        cls,
        task: WorkflowTask,
        context: ContextUnderstandingResult,
    ) -> tuple[WorkflowStep, ...]:
        """Generate deterministic task-driven workflow steps.

        Task intent determines which operations are required.
        Project context determines the most relevant targets.
        """

        targets = cls._relevant_targets(context)

        if not targets:
            targets = cls._fallback_targets(task)

        if not targets:
            targets = (".",)

        intent = cls._planning_intent(task)

        steps: list[WorkflowStep] = []

        # Inspection is always the first planning operation.
        for target in targets:
            steps.append(
                cls._build_step(
                    operation="inspect",
                    target=target,
                    context=context,
                )
            )

        # Analysis follows inspection.
        if intent["analysis"]:
            analysis_targets = cls._analysis_targets(
                task,
                context,
                targets,
            )

            for target in analysis_targets:
                steps.append(
                    cls._build_step(
                        operation="analyze",
                        target=target,
                        context=context,
                    )
                )

        # Dependency tracing follows inspection and analysis.
        if intent["dependencies"]:
            dependency_targets = cls._dependency_targets_for_task(
                task,
                context,
                targets,
            )

            for target in dependency_targets:
                steps.append(
                    cls._build_step(
                        operation="trace_dependencies",
                        target=target,
                        context=context,
                    )
                )

        return cls._normalize_step_ids(
            steps,
        )

    @staticmethod
    def _build_step(
        operation: str,
        target: str,
        context: ContextUnderstandingResult,
    ) -> WorkflowStep:
        """Build a non-executing deterministic workflow step."""

        return WorkflowStep(
            operation=operation,
            action=lambda: None,
            target=target,
            context=PlannerIntelligence._context_text(
                context,
            ),
        )

    @classmethod
    def _planning_intent(
        cls,
        task: WorkflowTask,
    ) -> dict[str, bool]:
        """Extract deterministic planning intent from task text."""

        text = (
            f"{task.description} "
            f"{task.context}"
        ).lower()

        tokens = {
            token.strip(".,:;!?()[]{}\"'")
            for token in text.split()
        }

        analysis = bool(
            tokens.intersection(
                cls._ANALYSIS_KEYWORDS,
            )
        )

        dependencies = bool(
            tokens.intersection(
                cls._DEPENDENCY_KEYWORDS,
            )
        )

        if any(
            phrase in text
            for phrase in (
                "code structure",
                "project structure",
                "class structure",
                "module relationship",
                "module relationships",
                "understand the code",
                "understand the project",
            )
        ):
            analysis = True

        return {
            "analysis": analysis,
            "dependencies": dependencies,
        }

    @staticmethod
    def _relevant_targets(
        context: ContextUnderstandingResult,
    ) -> tuple[str, ...]:
        """Return relevant file targets in stable order."""

        targets = {
            str(path).replace("\\", "/")
            for path in context.relevant_files
            if isinstance(path, Path)
        }

        return tuple(
            sorted(targets),
        )

    @staticmethod
    def _fallback_targets(
        task: WorkflowTask,
    ) -> tuple[str, ...]:
        """Extract a simple explicit file target from task text.

        This is deliberately conservative. It only recognizes tokens
        that look like project file paths and does not inspect files.
        """

        text = (
            f"{task.description} "
            f"{task.context}"
        )

        candidates: set[str] = set()

        for raw_token in text.replace(",", " ").split():
            token = raw_token.strip(
                ".,:;!?()[]{}\"'"
            )

            if not token:
                continue

            if "/" in token or "\\" in token:
                candidates.add(
                    token.replace("\\", "/")
                )
                continue

            suffix = Path(token).suffix.lower()

            if suffix in {
                ".py",
                ".pyw",
                ".js",
                ".ts",
                ".tsx",
                ".jsx",
                ".java",
                ".c",
                ".h",
                ".cpp",
                ".hpp",
                ".cs",
                ".go",
                ".rs",
                ".rb",
                ".php",
            }:
                candidates.add(token)

        return tuple(
            sorted(candidates),
        )

    @classmethod
    def _analysis_targets(
        cls,
        task: WorkflowTask,
        context: ContextUnderstandingResult,
        targets: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Choose deterministic targets for analysis."""

        symbol_targets = cls._relevant_symbol_targets(
            context,
        )

        relationship_targets = cls._relationship_targets(
            context,
        )

        if symbol_targets or relationship_targets:
            combined = set(symbol_targets)
            combined.update(relationship_targets)

            return tuple(
                sorted(combined),
            )

        explicit_targets = cls._fallback_targets(
            task,
        )

        if explicit_targets:
            return explicit_targets

        return targets

    @classmethod
    def _dependency_targets_for_task(
        cls,
        task: WorkflowTask,
        context: ContextUnderstandingResult,
        targets: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Choose deterministic targets for dependency tracing."""

        dependency_targets = cls._dependency_targets(
            context,
        )

        if dependency_targets:
            return dependency_targets

        explicit_targets = cls._fallback_targets(
            task,
        )

        if explicit_targets:
            return explicit_targets

        return targets

    @staticmethod
    def _relevant_symbol_targets(
        context: ContextUnderstandingResult,
    ) -> tuple[str, ...]:
        """Return deterministic symbol targets."""

        names = {
            str(symbol.name)
            for symbol in context.relevant_symbols
            if getattr(symbol, "name", None)
        }

        return tuple(
            sorted(names),
        )

    @staticmethod
    def _relationship_targets(
        context: ContextUnderstandingResult,
    ) -> tuple[str, ...]:
        """Return deterministic relationship targets."""

        targets: set[str] = set()

        for relationship in context.relationships:
            source = getattr(
                relationship,
                "source",
                "",
            )
            target = getattr(
                relationship,
                "target",
                "",
            )

            if source:
                targets.add(
                    str(source),
                )

            if target:
                targets.add(
                    str(target),
                )

        return tuple(
            sorted(targets),
        )

    @staticmethod
    def _dependency_targets(
        context: ContextUnderstandingResult,
    ) -> tuple[str, ...]:
        """Return deterministic dependency targets."""

        return tuple(
            sorted(
                {
                    str(dependency)
                    for dependency in context.dependencies
                    if dependency
                }
            )
        )

    @staticmethod
    def _normalize_step_ids(
        steps: Iterable[WorkflowStep],
    ) -> tuple[WorkflowStep, ...]:
        """Assign stable sequential IDs without changing semantics."""

        normalized: list[WorkflowStep] = []

        for index, step in enumerate(
            steps,
            start=1,
        ):
            normalized.append(
                WorkflowStep(
                    operation=step.operation,
                    action=step.action,
                    risk=step.risk,
                    approval=step.approval,
                    target=step.target,
                    context=step.context,
                    step_id=f"step-{index:03d}",
                )
            )

        return tuple(normalized)

    @staticmethod
    def _inject_context(
        steps: Iterable[WorkflowStep],
        context: ContextUnderstandingResult,
    ) -> tuple[WorkflowStep, ...]:
        context_text = PlannerIntelligence._context_text(
            context,
        )

        enriched = []

        for step in steps:
            if not isinstance(step, WorkflowStep):
                raise TypeError(
                    "actions must contain WorkflowStep instances"
                )

            existing_context = step.context

            combined_context = (
                context_text
                if existing_context is None
                else f"{existing_context}; {context_text}"
            )

            enriched.append(
                WorkflowStep(
                    operation=step.operation,
                    action=step.action,
                    risk=step.risk,
                    approval=step.approval,
                    target=step.target,
                    context=combined_context,
                    step_id=step.step_id,
                )
            )

        return PlannerIntelligence._normalize_step_ids(
            enriched,
        )

    @staticmethod
    def _context_text(
        context: ContextUnderstandingResult,
    ) -> str:
        files = tuple(
            sorted(
                str(path).replace("\\", "/")
                for path in context.relevant_files
            )
        )

        dependencies = tuple(
            sorted(
                {
                    str(dependency)
                    for dependency in context.dependencies
                }
            )
        )

        symbols = tuple(
            sorted(
                {
                    str(symbol.name)
                    for symbol in context.relevant_symbols
                    if getattr(symbol, "name", None)
                }
            )
        )

        relationships = tuple(
            sorted(
                {
                    (
                        str(relationship.source),
                        str(relationship.target),
                        str(relationship.kind),
                    )
                    for relationship in context.relationships
                }
            )
        )

        summary = getattr(
            context,
            "summary",
            None,
        )

        return (
            f"relevant_files={files}; "
            f"relevant_symbols={symbols}; "
            f"dependencies={dependencies}; "
            f"relationships={relationships}; "
            f"summary={summary!r}"
        )


if __name__ == "__main__":
    raise SystemExit(
        "PlannerIntelligence is a library interface."
    )
