import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from application.models import PlanModel, StepModel
from ui.agent_adapter import AgentUIAdapter
from ui.agent_panel import AgentInteractionPanel
from ui.agent_state import (
    AgentHistoryState,
    AgentInteractionState,
)


class M219HistoryStateTests(unittest.TestCase):

    def _panel(self):
        panel = object.__new__(AgentInteractionPanel)

        panel.task_value = Mock()
        panel.task_description = Mock()

        panel.understanding_summary = Mock()
        panel.understanding_files = Mock()
        panel.understanding_symbols = Mock()
        panel.understanding_relationships = Mock()
        panel.understanding_dependencies = Mock()

        panel.plan_value = Mock()
        panel.plan_status = Mock()
        panel.plan_step_count = Mock()
        panel.plan_steps = Mock()

        panel.risk_approval_value = Mock()
        panel.risk_approval_step_count = Mock()
        panel.risk_approval_issues = Mock()
        panel.risk_approval_warnings = Mock()
        panel.risk_approval_steps = Mock()

        panel.execution_value = Mock()
        panel.execution_run_id = Mock()
        panel.execution_current_step = Mock()
        panel.execution_progress = Mock()
        panel.execution_failure = Mock()
        panel.execution_times = Mock()
        panel.execution_steps = Mock()

        panel.result_value = Mock()

        panel.history_status = Mock()
        panel.history_selected = Mock()
        panel.history_entries = Mock()

        panel._history_run_ids = ()
        panel._history_selection_callback = None

        return panel

    def test_empty_history_is_rendered(self):
        panel = self._panel()

        state = AgentInteractionState(
            history=AgentHistoryState()
        )

        panel.render(state)

        panel.history_status.configure.assert_called_once_with(
            text="Empty"
        )
        panel.history_selected.configure.assert_called_once_with(
            text="Selected run: ?"
        )
        panel.history_entries.delete.assert_called_once_with(
            0,
            "end",
        )
        self.assertEqual(panel._history_run_ids, ())

    def test_history_entries_are_rendered(self):
        panel = self._panel()

        entry = SimpleNamespace(
            run_id="run-001",
            task=SimpleNamespace(title="Build feature"),
            result=SimpleNamespace(status="SUCCESS"),
        )

        state = AgentInteractionState(
            history=AgentHistoryState(
                entries=(entry,),
                selected_run_id="run-001",
                status="Available",
            )
        )

        panel.render(state)

        self.assertEqual(
            panel._history_run_ids,
            ("run-001",),
        )
        panel.history_entries.insert.assert_called_once_with(
            "end",
            "run-001 | Build feature | SUCCESS",
        )
        panel.history_entries.selection_set.assert_called_once_with(0)

    def test_history_selection_uses_run_id_callback(self):
        panel = self._panel()
        callback = Mock()

        panel._history_run_ids = ("run-001", "run-002")
        panel._history_selection_callback = callback

        panel.history_entries.curselection.return_value = ()

        panel._on_history_selection(None)

        callback.assert_not_called()

        panel.history_entries.curselection.return_value = (1,)

        panel._on_history_selection(None)

        callback.assert_called_once_with("run-002")

    def test_history_entry_adapter_exposes_plan_operations(self):
        entry = SimpleNamespace(
            task=SimpleNamespace(
                description="Build feature",
            ),
            plan=PlanModel(
                task_id="task-001",
                project_id="project-001",
                steps=(
                    StepModel(
                        step_id="step-001",
                        operation="Inspect authentication",
                    ),
                ),
            ),
            run=SimpleNamespace(
                run_id="run-001",
            ),
            result=SimpleNamespace(
                status="SUCCESS",
            ),
            snapshot=SimpleNamespace(
                step_states={},
                run_status="SUCCESS",
                run_id="run-001",
                current_step=None,
                started_at=None,
                finished_at=None,
            ),
        )

        state = AgentUIAdapter.from_history_entry(entry)

        self.assertEqual(
            state.plan.steps,
            ("Inspect authentication",),
        )


if __name__ == "__main__":
    unittest.main()
