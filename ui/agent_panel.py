from pathlib import Path
import tkinter as tk
from tkinter import ttk

from ui.agent_state import AgentInteractionState
from ui.visual_system import AgentPanelVisualSystem, AgentStage
from ui.visual_renderer import VisualRenderer
from ui.visual_composition import DEFAULT_UX_COMPOSITION, UXComposition


class AgentInteractionPanel(ttk.LabelFrame):
    """Agent interaction panel with runtime control delegation."""

    section_titles = (
        "Agent",
        "Current Task",
        "Understanding",
        "Plan",
        "Risk / Approval",
        "Execution",
        "Result",
        "History",
    )

    def __init__(
        self,
        parent,
        state: AgentInteractionState | None = None,
        composition: UXComposition | None = None,
        controller=None,
    ) -> None:
        super().__init__(parent, text="Agent", padding=12)

        self.composition = composition or DEFAULT_UX_COMPOSITION
        self.visual_renderer = VisualRenderer(self, self.composition)
        self.controller = controller
        self._stage_frames = {}
        self._stage_titles = {}

        self.columnconfigure(0, weight=1)

        self.task_value = self._create_section(
            0,
            "Current Task",
            "No task",
            AgentStage.TASK,
        )

        self.task_description = self._create_section(
            1,
            "Description",
            "No task selected",
        )

        self._build_understanding_section(2)
        self._build_plan_section(3)
        self._build_risk_approval_section(4)
        self._build_execution_section(5)

        self.result_value = self._create_section(
            6,
            "Result",
            "No result available",
            AgentStage.RESULT,
        )

        self._build_history_section(7)
        self._build_runtime_controls(8)
        self.visual_system = AgentPanelVisualSystem(
            self,
            self._stage_frames,
            self._stage_titles,
        )

        self.render(
            state
            if isinstance(state, AgentInteractionState)
            else AgentInteractionState()
        )

    def set_controller(self, controller) -> None:
        """Attach the application controller used by runtime controls."""
        self.controller = controller
        self._update_runtime_controls()

    def _create_section(
        self,
        row: int,
        title: str,
        value: str,
        stage: AgentStage | None = None,
    ) -> ttk.Label:
        frame = ttk.Frame(self)
        frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        frame.columnconfigure(0, weight=1)
        if stage is not None:
            self._stage_frames[stage] = frame

        title_label = ttk.Label(frame, text=title)
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 3),
        )
        self.visual_renderer.apply_text_label(title_label)
        if stage is not None:
            self._stage_titles[stage] = title_label

        value_label = ttk.Label(
            frame,
            text=value,
            anchor="w",
        )
        value_label.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        self.visual_renderer.apply_text_label(value_label)

        return value_label

    def _build_understanding_section(self, row: int) -> None:
        frame = ttk.Frame(self)
        frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        frame.columnconfigure(0, weight=1)
        self._stage_frames[AgentStage.UNDERSTANDING] = frame

        title_label = ttk.Label(frame, text="Understanding")
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 3),
        )
        self.visual_renderer.apply_text_label(title_label)
        self._stage_titles[AgentStage.UNDERSTANDING] = title_label

        self.understanding_summary = self._create_understanding_label(
            frame, 1, "No understanding available"
        )
        self.understanding_files = self._create_understanding_label(
            frame, 2, "Files: 0"
        )
        self.understanding_symbols = self._create_understanding_label(
            frame, 3, "Symbols: 0"
        )
        self.understanding_relationships = self._create_understanding_label(
            frame, 4, "Relationships: 0"
        )
        self.understanding_dependencies = self._create_understanding_label(
            frame, 5, "Dependencies: 0"
        )

    def _create_understanding_label(
        self,
        frame: ttk.Frame,
        row: int,
        value: str,
    ) -> ttk.Label:
        label = ttk.Label(frame, text=value, anchor="w")
        label.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(1, 1),
        )
        self.visual_renderer.apply_text_label(label)
        return label

    def _build_plan_section(self, row: int) -> None:
        frame = ttk.Frame(self)
        frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        frame.columnconfigure(0, weight=1)
        self._stage_frames[AgentStage.PLAN] = frame

        title_label = ttk.Label(frame, text="Plan")
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 3),
        )
        self.visual_renderer.apply_text_label(title_label)
        self._stage_titles[AgentStage.PLAN] = title_label

        self.plan_value = ttk.Label(
            frame,
            text="No plan available",
            anchor="w",
        )
        self.plan_value.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        self.visual_renderer.apply_text_label(self.plan_value)

        self.plan_summary = self.plan_value

        self.plan_status = ttk.Label(
            frame,
            text="No plan",
            anchor="w",
        )
        self.plan_status.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(2, 2),
        )
        self.visual_renderer.apply_text_label(self.plan_status)

        self.plan_step_count = ttk.Label(
            frame,
            text="0 steps",
            anchor="w",
        )
        self.plan_step_count.grid(
            row=3,
            column=0,
            sticky="ew",
        )
        self.visual_renderer.apply_text_label(self.plan_step_count)

        self.plan_steps = tk.Listbox(
            frame,
            state=tk.DISABLED,
            height=4,
            activestyle="none",
        )
        self.plan_steps.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

    def _build_risk_approval_section(self, row: int) -> None:
        frame = ttk.Frame(self)
        frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        frame.columnconfigure(0, weight=1)
        self._stage_frames[AgentStage.APPROVAL] = frame

        title_label = ttk.Label(frame, text="Risk / Approval")
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 3),
        )
        self.visual_renderer.apply_text_label(title_label)
        self._stage_titles[AgentStage.APPROVAL] = title_label

        self.risk_approval_value = ttk.Label(
            frame,
            text="Not ready",
            anchor="w",
        )
        self.risk_approval_value.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        self.visual_renderer.apply_text_label(self.risk_approval_value)

        self.risk_approval_step_count = ttk.Label(
            frame,
            text="0 assessed steps",
            anchor="w",
        )
        self.risk_approval_step_count.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(2, 2),
        )
        self.visual_renderer.apply_text_label(
            self.risk_approval_step_count
        )

        self.risk_approval_issues = ttk.Label(
            frame,
            text="Issues: 0",
            anchor="w",
        )
        self.risk_approval_issues.grid(
            row=3,
            column=0,
            sticky="ew",
        )
        self.visual_renderer.apply_text_label(
            self.risk_approval_issues
        )

        self.risk_approval_warnings = ttk.Label(
            frame,
            text="Warnings: 0",
            anchor="w",
        )
        self.risk_approval_warnings.grid(
            row=4,
            column=0,
            sticky="ew",
        )
        self.visual_renderer.apply_text_label(
            self.risk_approval_warnings
        )

        self.risk_approval_steps = tk.Listbox(
            frame,
            state=tk.DISABLED,
            height=4,
            activestyle="none",
        )
        self.risk_approval_steps.grid(
            row=5,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

    def _build_history_section(self, row: int) -> None:
        frame = ttk.Frame(self)
        frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        frame.columnconfigure(0, weight=1)
        self._stage_frames[AgentStage.EXECUTION] = frame

        title_label = ttk.Label(frame, text="History")
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 3),
        )
        self.visual_renderer.apply_text_label(title_label)
        self._stage_titles[AgentStage.EXECUTION] = title_label

        self.history_status = ttk.Label(
            frame,
            text="Empty",
            anchor="w",
        )
        self.history_status.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        self.visual_renderer.apply_text_label(self.history_status)

        self.history_selected = ttk.Label(
            frame,
            text="Selected run: ?",
            anchor="w",
        )
        self.history_selected.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(2, 2),
        )
        self.visual_renderer.apply_text_label(self.history_selected)

        self.history_entries = tk.Listbox(
            frame,
            state=tk.DISABLED,
            height=5,
            activestyle="none",
        )
        self.history_entries.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )
        self.history_entries.bind(
            "<<ListboxSelect>>",
            self._on_history_selection,
        )

        self._history_run_ids: tuple[str, ...] = ()
        self._history_selection_callback = None

    def set_history_selection_callback(self, callback) -> None:
        self._history_selection_callback = callback

    def _on_history_selection(self, _event: tk.Event) -> None:
        if self._history_selection_callback is None:
            return

        selection = self.history_entries.curselection()
        if not selection:
            return

        index = selection[0]
        if index >= len(self._history_run_ids):
            return

        self._history_selection_callback(self._history_run_ids[index])

    def _build_execution_section(self, row: int) -> None:
        frame = ttk.Frame(self)
        frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(frame, text="Execution")
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 3),
        )
        self.visual_renderer.apply_text_label(title_label)

        self.execution_value = self._create_execution_label(
            frame, 1, "Idle"
        )
        self.execution_run_id = self._create_execution_label(
            frame, 2, "Run ID: -"
        )
        self.execution_current_step = self._create_execution_label(
            frame, 3, "Current step: -"
        )
        self.execution_progress = self._create_execution_label(
            frame, 4, "Progress: 0%"
        )
        self.execution_failure = self._create_execution_label(
            frame, 5, "Failure: -"
        )
        self.execution_times = self._create_execution_label(
            frame,
            6,
            "Started: - | Finished: -",
        )

        self.execution_steps = tk.Listbox(
            frame,
            state=tk.DISABLED,
            height=4,
            activestyle="none",
        )
        self.execution_steps.grid(
            row=7,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

    def _create_execution_label(
        self,
        frame: ttk.Frame,
        row: int,
        value: str,
    ) -> ttk.Label:
        label = ttk.Label(
            frame,
            text=value,
            anchor="w",
        )
        label.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(1, 1),
        )
        self.visual_renderer.apply_text_label(label)
        return label

    def _build_runtime_controls(self, row: int) -> None:
        frame = ttk.Frame(self)
        frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(frame, text="Runtime Control")
        title_label.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(0, 3),
        )
        self.visual_renderer.apply_text_label(title_label)

        self.runtime_status = ttk.Label(
            frame,
            text="Runtime: unavailable",
            anchor="w",
        )
        self.runtime_status.grid(
            row=1,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(0, 5),
        )
        self.visual_renderer.apply_text_label(self.runtime_status)

        self.start_button = ttk.Button(
            frame,
            text="Start",
            command=self._on_start,
        )
        self.start_button.grid(row=2, column=0, padx=(0, 4))

        self.pause_button = ttk.Button(
            frame,
            text="Pause",
            command=self._on_pause,
        )
        self.pause_button.grid(row=2, column=1, padx=4)

        self.resume_button = ttk.Button(
            frame,
            text="Resume",
            command=self._on_resume,
        )
        self.resume_button.grid(row=2, column=2, padx=4)

        self.terminate_button = ttk.Button(
            frame,
            text="Terminate",
            command=self._on_terminate,
        )
        self.terminate_button.grid(row=2, column=3, padx=(4, 0))

        self._update_runtime_controls()

    def _update_runtime_controls(self) -> None:
        available = self.controller is not None

        for button in (
            self.start_button,
            self.pause_button,
            self.resume_button,
            self.terminate_button,
        ):
            button.configure(
                state=tk.NORMAL if available else tk.DISABLED
            )

        if not available:
            self.runtime_status.configure(
                text="Runtime: unavailable"
            )

    def _on_start(self) -> None:
        if self.controller is None:
            return

        self.controller.start_agent_task(
            self._current_state.task,
            self._current_state.plan.steps,
        )
        self._refresh_runtime_status()

    def _on_pause(self) -> None:
        if self.controller is None:
            return

        self.controller.pause_agent()
        self._refresh_runtime_status()

    def _on_resume(self) -> None:
        if self.controller is None:
            return

        self.controller.resume_agent()
        self._refresh_runtime_status()

    def _on_terminate(self) -> None:
        if self.controller is None:
            return

        self.controller.terminate_agent()
        self._refresh_runtime_status()

    def _refresh_runtime_status(self) -> None:
        if self.controller is None:
            return

        status = self.controller.agent_runtime_status()

        if hasattr(self, "runtime_status"):
            self.runtime_status.configure(
                text=f"Runtime: {status}"
            )

    def render(self, state: AgentInteractionState) -> None:
        """Render Agent state without executing Agent work."""

        self._current_state = state
        visual_system = getattr(self, "visual_system", None)
        if visual_system is not None:
            visual_system.render(state)

        self.task_value.configure(text=state.task.title)
        self.task_description.configure(text=state.task.description)

        self.understanding_summary.configure(
            text=state.understanding.summary
        )
        self.understanding_files.configure(
            text=f"Files: {len(state.understanding.relevant_files)}"
        )
        self.understanding_symbols.configure(
            text=f"Symbols: {len(state.understanding.relevant_symbols)}"
        )
        self.understanding_relationships.configure(
            text=f"Relationships: {len(state.understanding.relationships)}"
        )
        self.understanding_dependencies.configure(
            text=f"Dependencies: {len(state.understanding.dependencies)}"
        )

        self.plan_value.configure(text=state.plan.summary)
        self.plan_status.configure(text=state.plan.status)
        self.plan_step_count.configure(
            text=f"{len(state.plan.steps)} steps"
        )

        self.plan_steps.configure(state=tk.NORMAL)
        self.plan_steps.delete(0, tk.END)
        for step in state.plan.steps:
            self.plan_steps.insert(tk.END, step)
        self.plan_steps.configure(state=tk.DISABLED)

        risk_approval = state.risk_approval

        self.risk_approval_value.configure(
            text="Ready" if risk_approval.ready else "Not ready"
        )
        self.risk_approval_step_count.configure(
            text=f"{len(risk_approval.steps)} assessed steps"
        )
        self.risk_approval_issues.configure(
            text=f"Issues: {len(risk_approval.issues)}"
        )
        self.risk_approval_warnings.configure(
            text=f"Warnings: {len(risk_approval.warnings)}"
        )

        self.risk_approval_steps.configure(state=tk.NORMAL)
        self.risk_approval_steps.delete(0, tk.END)

        for step in risk_approval.steps:
            self.risk_approval_steps.insert(
                tk.END,
                (
                    f"{step.step_id} | "
                    f"Risk={step.risk} | "
                    f"Approval={step.approval} | "
                    f"Readiness={step.readiness} | "
                    f"Ready={step.ready} | "
                    f"{step.reason}"
                ),
            )

        self.risk_approval_steps.configure(state=tk.DISABLED)

        execution = state.execution

        self.execution_value.configure(text=execution.status)
        self.execution_run_id.configure(
            text=f"Run ID: {execution.run_id or '-'}"
        )
        self.execution_current_step.configure(
            text=f"Current step: {execution.current_step or '-'}"
        )
        self.execution_progress.configure(
            text=f"Progress: {execution.progress}%"
        )
        self.execution_failure.configure(
            text=f"Failure: {execution.failure_reason or '-'}"
        )
        self.execution_times.configure(
            text=(
                f"Started: {execution.started_at or '-'}"
                f" | Finished: {execution.finished_at or '-'}"
            )
        )

        self.execution_steps.configure(state=tk.NORMAL)
        self.execution_steps.delete(0, tk.END)

        for step in execution.step_states:
            self.execution_steps.insert(tk.END, step)

        self.execution_steps.configure(state=tk.DISABLED)

        self.result_value.configure(text=state.result.summary)

        history = state.history

        self.history_status.configure(text=history.status)
        self.history_selected.configure(
            text=f"Selected run: {history.selected_run_id or '?'}"
        )

        self._history_run_ids = tuple(
            entry.run_id for entry in history.entries
        )

        self.history_entries.configure(state=tk.NORMAL)
        self.history_entries.delete(0, tk.END)

        for entry in history.entries:
            task_title = getattr(
                entry.task,
                "title",
                getattr(entry.task, "description", ""),
            )
            self.history_entries.insert(
                tk.END,
                f"{entry.run_id} | {task_title} | {entry.result.status}",
            )

        if history.selected_run_id in self._history_run_ids:
            selected_index = self._history_run_ids.index(
                history.selected_run_id
            )
            self.history_entries.selection_set(selected_index)
            self.history_entries.see(selected_index)

        self.history_entries.configure(state=tk.DISABLED)

        if getattr(self, "controller", None) is not None:
            self._refresh_runtime_status()


__all__ = ["AgentInteractionPanel"]
