import unittest
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import tempfile
from unittest.mock import patch

from agent_workflow.agent_service import AgentService
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from application.models import TaskModel
from application.services import ApplicationExecutionService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService
from ui.animation_accessibility import (
    AnimationAccessibility,
    MotionMode,
    MotionPolicy,
)
from ui.agent_adapter import AgentUIAdapter
from ui.agent_state import (
    AgentExecutionState,
    AgentInteractionState,
    AgentPlanState,
    AgentResultState,
    AgentRiskApprovalState,
    AgentRiskApprovalStepState,
    AgentTaskState,
    AgentUnderstandingState,
)
from ui.agent_transitions import AgentVisualState
from ui.animation import AnimationKind
from ui.agent_panel import AgentInteractionPanel
from ui.app import CodingAssistantApp
from ui.visual_system import (
    AgentStage,
    AgentVisualSystem,
    StageEffect,
)
from ui.pointer_visuals import PointerVisualLayer
from ui.workspace_empty_state import WorkspaceEmptyState


class M251AgentVisualSystemTests(unittest.TestCase):
    def setUp(self):
        self.visual_system = AgentVisualSystem()

    def test_empty_agent_state_is_idle(self):
        projection = self.visual_system.project(AgentInteractionState())

        self.assertEqual(projection.stage, AgentStage.IDLE)
        self.assertEqual(projection.effect, StageEffect.REST)

    def test_running_agent_state_focuses_execution(self):
        state = AgentInteractionState(
            execution=AgentExecutionState(status="RUNNING"),
        )

        projection = self.visual_system.project(state)

        self.assertEqual(projection.stage, AgentStage.EXECUTION)
        self.assertEqual(projection.effect, StageEffect.RUNNING)

    def test_plan_to_approval_uses_existing_m22_transition(self):
        plan_state = AgentInteractionState(
            plan=AgentPlanState(
                summary="1 step",
                status="Ready",
                steps=("inspect",),
            ),
        )
        approval_state = AgentInteractionState(
            plan=plan_state.plan,
            risk_approval=AgentRiskApprovalState(
                ready=False,
                steps=(
                    AgentRiskApprovalStepState(
                        step_id="step-1",
                        risk="HIGH_RISK",
                        approval="NOT_REQUESTED",
                        readiness="BLOCKED",
                        reason="high-risk step requires approval",
                        ready=False,
                    ),
                ),
            ),
        )

        previous = self.visual_system.project(plan_state)
        transition = self.visual_system.transition(
            previous,
            approval_state,
        )

        self.assertEqual(previous.workflow_state, AgentVisualState.PLAN_READY)
        self.assertEqual(
            transition.target.workflow_state,
            AgentVisualState.WAITING_APPROVAL,
        )
        self.assertEqual(transition.target.stage, AgentStage.APPROVAL)
        self.assertEqual(transition.target.effect, StageEffect.WAITING)
        self.assertEqual(transition.animation.kind, AnimationKind.PULSE)

    def test_success_and_error_are_localized_to_result_stage(self):
        success = self.visual_system.project(
            AgentInteractionState(
                result=AgentResultState(
                    summary="Completed",
                    status="SUCCESS",
                ),
            )
        )
        failure = self.visual_system.project(
            AgentInteractionState(
                execution=AgentExecutionState(status="FAILED"),
                result=AgentResultState(
                    summary="Failed",
                    status="FAILED",
                ),
            )
        )

        self.assertEqual(success.stage, AgentStage.RESULT)
        self.assertEqual(success.effect, StageEffect.SUCCESS)
        self.assertEqual(failure.stage, AgentStage.RESULT)
        self.assertEqual(failure.effect, StageEffect.ERROR)

    def test_full_agent_state_sequence_maps_through_m22_rules(self):
        task = AgentInteractionState(
            task=AgentTaskState(
                title="Inspect project",
                description="Inspect the selected project",
                status="READY",
            ),
        )
        understanding = AgentInteractionState(
            task=task.task,
            understanding=AgentUnderstandingState(
                summary="Project context ready",
                relevant_files=("main.py",),
            ),
        )
        plan = AgentInteractionState(
            task=task.task,
            understanding=understanding.understanding,
            plan=AgentPlanState(
                summary="1 step",
                status="Ready",
                steps=("inspect",),
            ),
            risk_approval=AgentRiskApprovalState(ready=True),
        )
        approval = AgentInteractionState(
            task=task.task,
            understanding=understanding.understanding,
            plan=plan.plan,
            risk_approval=AgentRiskApprovalState(
                ready=False,
                steps=(
                    AgentRiskApprovalStepState(
                        step_id="step-1",
                        risk="HIGH_RISK",
                        approval="NOT_REQUESTED",
                        readiness="BLOCKED",
                        reason="approval required",
                        ready=False,
                    ),
                ),
            ),
        )
        running = AgentInteractionState(
            task=task.task,
            plan=plan.plan,
            execution=AgentExecutionState(status="RUNNING"),
        )
        success = AgentInteractionState(
            task=task.task,
            plan=plan.plan,
            execution=AgentExecutionState(status="COMPLETED"),
            result=AgentResultState(summary="Completed", status="SUCCESS"),
        )
        states = (task, understanding, plan, approval, running, success)
        expected = (
            AgentVisualState.PROCESSING,
            AgentVisualState.UNDERSTANDING_READY,
            AgentVisualState.PLAN_READY,
            AgentVisualState.WAITING_APPROVAL,
            AgentVisualState.EXECUTING,
            AgentVisualState.COMPLETED,
        )

        root = tk.Tk()
        root.withdraw()
        panel = AgentInteractionPanel(root)
        try:
            previous = None
            for state, expected_state in zip(states, expected):
                transition = self.visual_system.transition(previous, state)
                panel.render(state)
                self.assertEqual(
                    transition.target.workflow_state,
                    expected_state,
                )
                self.assertNotEqual(
                    transition.animation.kind,
                    AnimationKind.NONE,
                )
                self.assertEqual(
                    panel.visual_system.previous.stage,
                    transition.target.stage,
                )
                active_regions = tuple(
                    stage
                    for stage, outline in panel.visual_system.outlines.items()
                    if outline.effect is not StageEffect.REST
                )
                self.assertEqual(active_regions, (transition.target.stage,))
                previous = transition.target

            failure = AgentInteractionState(
                task=task.task,
                plan=plan.plan,
                execution=AgentExecutionState(status="FAILED"),
                result=AgentResultState(
                    summary="Failed",
                    status="FAILED",
                ),
            )
            panel.render(running)
            panel.render(failure)
            self.assertEqual(
                panel.visual_system.previous.workflow_state,
                AgentVisualState.FAILED,
            )
            self.assertEqual(
                panel.visual_system.outlines[AgentStage.RESULT].effect,
                StageEffect.ERROR,
            )
        finally:
            root.destroy()

    def test_real_application_execution_drives_success_and_error_visuals(self):
        root = tk.Tk()
        root.withdraw()
        panel = AgentInteractionPanel(root)
        try:
            for should_fail, expected_effect in (
                (False, StageEffect.SUCCESS),
                (True, StageEffect.ERROR),
            ):
                with self.subTest(should_fail=should_fail), tempfile.TemporaryDirectory() as directory:
                    project = Path(directory)
                    snapshot_store = SnapshotStore(project, project / "snapshots")
                    workflow = AgentWorkflow(
                        history_store=HistoryStore(project / "history.json"),
                        snapshot_service=SnapshotService(
                            project,
                            store=snapshot_store,
                        ),
                    )
                    agent_service = AgentService(WorkflowService(workflow))
                    execution_service = ApplicationExecutionService(agent_service)

                    def action():
                        if should_fail:
                            raise RuntimeError("controlled visual-state failure")
                        return "ok"

                    execution = execution_service.run(
                        TaskModel(
                            task_id="m25-visual-task",
                            project_id="m25-project",
                            description="Verify visual outcome",
                        ),
                        (WorkflowStep("inspect", action, target="main.py"),),
                    )
                    state = AgentUIAdapter.from_execution(execution)
                    panel.render(state)

                    self.assertEqual(
                        panel.visual_system.previous.stage,
                        AgentStage.RESULT,
                    )
                    self.assertEqual(
                        panel.visual_system.previous.effect,
                        expected_effect,
                    )
        finally:
            root.destroy()


class M251PanelVisualConnectionTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_render_focuses_only_the_running_execution_region(self):
        panel = AgentInteractionPanel(self.root)
        state = AgentInteractionState(
            execution=AgentExecutionState(status="RUNNING"),
        )

        panel.render(state)

        self.assertEqual(
            panel.visual_system.previous.stage,
            AgentStage.EXECUTION,
        )
        self.assertEqual(
            panel.visual_system.outlines[AgentStage.EXECUTION].effect,
            StageEffect.RUNNING,
        )
        self.assertEqual(
            panel.visual_system.outlines[AgentStage.PLAN].effect,
            StageEffect.REST,
        )


class M251ProjectTreeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.project_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.project_directory.name)

    def tearDown(self):
        self.root.destroy()
        self.project_directory.cleanup()

    def test_selected_user_project_is_shown_without_runtime_artifacts(self):
        (self.project / "main.py").write_text("print('project')", encoding="utf-8")
        for filename in ("runtime.dll", "module.pyd", "helper.exe", "bytecode.pyc"):
            (self.project / filename).write_bytes(b"runtime")
        for dirname in (
            "_internal",
            "build",
            "dist",
            "site-packages",
            "runtime",
            ".git",
            ".venv",
            "__pycache__",
        ):
            (self.project / dirname).mkdir()
        (self.project / "src").mkdir()
        (self.project / "src" / "feature.py").write_text(
            "value = 1",
            encoding="utf-8",
        )

        app = CodingAssistantApp(self.root)
        with patch(
            "ui.app.filedialog.askdirectory",
            return_value=str(self.project),
        ):
            app._choose_project()

        self.assertEqual(app.controller.project_context.path, self.project.resolve())
        tree_root = app.tree_view.get_children()[0]
        visible_nodes = {
            app.tree_view.item(item, "text")
            for item in app.tree_view.get_children(tree_root)
        }
        self.assertEqual(visible_nodes, {"main.py", "src"})

    def test_shell_starts_without_treating_runtime_as_a_project(self):
        app = CodingAssistantApp(self.root)

        self.assertIsNone(app.controller.project_context.path)
        self.assertEqual(app.empty_state.winfo_manager(), "grid")
        self.assertEqual(app.file_viewer.winfo_manager(), "")
        self.assertEqual(
            app.status_label.cget("text"),
            "Open a project to begin",
        )


class M251ReducedMotionTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_workspace_ambient_motion_obeys_m22_reduced_policy(self):
        accessibility = AnimationAccessibility(
            MotionPolicy(mode=MotionMode.REDUCED)
        )
        empty_state = WorkspaceEmptyState(
            self.root,
            accessibility=accessibility,
        )

        self.assertTrue(accessibility.reduced_motion)
        self.assertIsNone(empty_state._ambient_after)
        empty_state.set_agent_active(True)
        empty_state.set_agent_active(False)
        self.assertIsNone(empty_state._ambient_after)


class M251ShellVisualFoundationTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_entire_empty_shell_uses_the_shared_cold_palette(self):
        app = CodingAssistantApp(self.root)
        self.root.update_idletasks()
        tokens = app.composition.tokens
        style = ttk.Style(self.root)

        self.assertEqual(style.theme_use(), "clam")
        self.assertEqual(self.root.title(), "PacePilot")
        self.assertEqual(self.root.cget("background"), tokens.colors["background"])
        self.assertEqual(
            app.project_panel.cget("style"),
            "PacePilot.Panel.TLabelframe",
        )
        self.assertEqual(
            app.workspace_panel.cget("style"),
            "PacePilot.Panel.TLabelframe",
        )
        self.assertEqual(
            app.agent_panel.cget("style"),
            "PacePilot.Panel.TLabelframe",
        )
        self.assertEqual(
            app.content_pane.cget("style"),
            "PacePilot.TPanedwindow",
        )
        self.assertEqual(
            app.open_project_button.cget("style"),
            "PacePilot.Primary.TButton",
        )
        self.assertIn(
            str(app.icons.image("folder")),
            str(app.open_project_button.cget("image")),
        )
        self.assertIn(
            str(app.icons.image("folder")),
            str(app.project_heading.cget("image")),
        )
        self.assertIn(
            str(app.icons.image("workspace")),
            str(app.workspace_heading.cget("image")),
        )
        self.assertIn(
            str(app.icons.image("agent")),
            str(app.agent_panel.heading_label.cget("image")),
        )
        self.assertTrue(
            all(
                (app.icons.image(name).width(), app.icons.image(name).height())
                == (16, 16)
                for name in app.icons.names()
            )
        )
        self.assertNotEqual(
            style.lookup("PacePilot.Primary.TButton", "background"),
            tokens.colors["accent_blue"],
        )
        self.assertEqual(
            app.project_context_label.cget("text"),
            "No project open",
        )
        self.assertEqual(
            app.file_viewer.cget("background"),
            tokens.colors["surface"],
        )
        self.assertEqual(
            app.agent_panel.plan_steps.cget("background"),
            tokens.colors["surface"],
        )
        for listbox in (
            app.agent_panel.plan_steps,
            app.agent_panel.risk_approval_steps,
            app.agent_panel.execution_steps,
            app.agent_panel.history_entries,
        ):
            self.assertEqual(
                listbox.cget("background"),
                tokens.colors["surface"],
            )
        self.assertEqual(
            style.lookup("PacePilot.M25Stage.TFrame", "background"),
            tokens.colors["surface_elevated"],
        )
        for stage, icon_name in (
            (AgentStage.TASK, "task"),
            (AgentStage.UNDERSTANDING, "understanding"),
            (AgentStage.PLAN, "plan"),
            (AgentStage.APPROVAL, "approval"),
            (AgentStage.EXECUTION, "execution"),
            (AgentStage.RESULT, "result"),
        ):
            self.assertIn(
                str(app.icons.image(icon_name)),
                str(app.agent_panel._stage_titles[stage].cget("image")),
            )
        self.assertEqual(
            app.empty_state.cget("background"),
            tokens.colors["background"],
        )
        self.assertEqual(
            app.agent_panel.visual_system.idle_outline.effect,
            StageEffect.IDLE,
        )
        self.assertIsNotNone(app.agent_panel.visual_system.idle_outline._after_id)
        self.assertIsNotNone(app.empty_state._ambient_after)
        self.assertIsNone(app.controller.project_context.path)

    def test_shared_reduced_motion_freezes_idle_shell_animations(self):
        accessibility = AnimationAccessibility(
            MotionPolicy(mode=MotionMode.REDUCED)
        )
        app = CodingAssistantApp(
            self.root,
            accessibility=accessibility,
        )

        self.assertIsNone(app.empty_state._ambient_after)
        self.assertIsNone(app.agent_panel.visual_system.idle_outline._after_id)
        self.assertTrue(accessibility.reduced_motion)

    def test_pointer_motion_uses_tk_loop_and_focus_loss_clears_glow(self):
        self.root.deiconify()
        self.root.geometry("1000x700")
        app = CodingAssistantApp(self.root)
        self.root.focus_force()
        self.root.update()
        layer = app.pointer_layer

        self.assertTrue(layer.enabled)
        self.assertTrue(layer.focused)
        self.assertIn(str(app.header_frame), layer._surfaces)
        self.assertIn(str(app.project_panel), layer._surfaces)
        self.assertIn(str(app.workspace_panel), layer._surfaces)
        self.assertIn(str(app.agent_panel), layer._surfaces)
        self.assertIn(str(app.empty_state), layer._surfaces)
        self.assertIn(str(app.tree_view), layer._surfaces)

        app.empty_state.event_generate(
            "<Motion>",
            x=max(1, app.empty_state.winfo_width() // 2),
            y=max(1, app.empty_state.winfo_height() // 2),
            warp=True,
        )
        self.assertIsNotNone(layer._after_id)
        self.root.after(100, self.root.quit)
        self.root.mainloop()

        self.assertGreater(app.empty_state._pointer_intensity, 0)
        self.assertIsNotNone(app.empty_state._pointer_items)
        self.root.event_generate("<FocusOut>")
        self.root.update()
        self.assertFalse(layer.focused)
        self.assertEqual(app.empty_state._pointer_intensity, 0)

    def test_reduced_motion_disables_pointer_bindings_and_dispatch(self):
        accessibility = AnimationAccessibility(
            MotionPolicy(mode=MotionMode.REDUCED)
        )
        app = CodingAssistantApp(
            self.root,
            accessibility=accessibility,
        )

        self.assertFalse(app.pointer_layer.enabled)
        self.assertIsNone(app.pointer_layer._after_id)
        self.assertIsNone(app.empty_state._ambient_after)

    def test_pointer_highlight_is_local_to_primary_and_agent_surfaces(self):
        self.root.deiconify()
        self.root.geometry("1000x700")
        app = CodingAssistantApp(self.root)
        self.root.focus_force()
        self.root.update()

        app.open_project_button.event_generate(
            "<Motion>",
            x=4,
            y=4,
            warp=True,
        )
        self.root.after(100, self.root.quit)
        self.root.mainloop()

        self.assertIn("Pointer", app.open_project_button.cget("style"))
        self.assertEqual(
            app.project_panel.cget("style"),
            "PacePilot.Panel.TLabelframe",
        )

        task_heading = app.agent_panel._stage_titles[AgentStage.TASK]
        task_heading.event_generate(
            "<Motion>",
            x=4,
            y=4,
            warp=True,
        )
        self.root.after(100, self.root.quit)
        self.root.mainloop()

        self.assertIsNotNone(app.pointer_layer._current)
        self.assertEqual(
            app.pointer_layer._current.widget,
            app.agent_panel._stage_frames[AgentStage.TASK],
        )
        self.assertGreater(
            app.agent_panel.visual_system.outlines[AgentStage.TASK]._pointer_intensity,
            0,
        )
        self.assertEqual(
            app.agent_panel.visual_system.outlines[AgentStage.PLAN].effect,
            StageEffect.REST,
        )


if __name__ == "__main__":
    unittest.main()