import tkinter as tk
import unittest

from ui.agent_panel import AgentInteractionPanel
from ui.agent_state import (
    AgentInteractionState,
    AgentRiskApprovalState,
    AgentRiskApprovalStepState,
)


class M218RiskApprovalPresentationTests(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_panel_contains_risk_approval_section(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )

        self.assertIn("Risk / Approval", panel.section_titles)

    def test_empty_risk_approval_state_is_rendered(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )

        self.assertEqual(
            panel.risk_approval_value.cget("text"),
            "Not ready",
        )
        self.assertEqual(
            panel.risk_approval_step_count.cget("text"),
            "0 assessed steps",
        )
        self.assertEqual(
            panel.risk_approval_issues.cget("text"),
            "Issues: 0",
        )
        self.assertEqual(
            panel.risk_approval_warnings.cget("text"),
            "Warnings: 0",
        )

    def test_ready_risk_approval_state_is_presented(self):
        state = AgentInteractionState(
            risk_approval=AgentRiskApprovalState(
                ready=True,
                steps=(
                    AgentRiskApprovalStepState(
                        step_id="step-001",
                        risk="SAFE",
                        approval="NOT_REQUESTED",
                        readiness="READY",
                        reason="step is ready",
                        ready=True,
                    ),
                ),
            )
        )

        panel = AgentInteractionPanel(self.root, state)

        self.assertEqual(
            panel.risk_approval_value.cget("text"),
            "Ready",
        )
        self.assertEqual(
            panel.risk_approval_step_count.cget("text"),
            "1 assessed steps",
        )

        items = panel.risk_approval_steps.get(0, tk.END)

        self.assertEqual(len(items), 1)
        self.assertIn("step-001", items[0])
        self.assertIn("Risk=SAFE", items[0])
        self.assertIn("Approval=NOT_REQUESTED", items[0])
        self.assertIn("Readiness=READY", items[0])
        self.assertIn("Ready=True", items[0])

    def test_blocked_risk_approval_state_is_presented(self):
        state = AgentInteractionState(
            risk_approval=AgentRiskApprovalState(
                ready=False,
                steps=(
                    AgentRiskApprovalStepState(
                        step_id="step-001",
                        risk="HIGH_RISK",
                        approval="DENIED",
                        readiness="BLOCKED",
                        reason="approval status blocks execution",
                        ready=False,
                    ),
                ),
                issues=("approval status blocks execution",),
                warnings=("high-risk step",),
            )
        )

        panel = AgentInteractionPanel(self.root, state)

        self.assertEqual(
            panel.risk_approval_value.cget("text"),
            "Not ready",
        )
        self.assertEqual(
            panel.risk_approval_issues.cget("text"),
            "Issues: 1",
        )
        self.assertEqual(
            panel.risk_approval_warnings.cget("text"),
            "Warnings: 1",
        )

        items = panel.risk_approval_steps.get(0, tk.END)

        self.assertEqual(len(items), 1)
        self.assertIn("Risk=HIGH_RISK", items[0])
        self.assertIn("Approval=DENIED", items[0])
        self.assertIn("Readiness=BLOCKED", items[0])
        self.assertIn("Ready=False", items[0])
        self.assertIn("approval status blocks execution", items[0])

    def test_render_updates_risk_approval_state(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )

        state = AgentInteractionState(
            risk_approval=AgentRiskApprovalState(
                ready=True,
                steps=(
                    AgentRiskApprovalStepState(
                        step_id="step-002",
                        risk="SAFE",
                        approval="APPROVED",
                        readiness="READY",
                        reason="approved",
                        ready=True,
                    ),
                ),
                issues=(),
                warnings=(),
            )
        )

        panel.render(state)

        self.assertEqual(
            panel.risk_approval_value.cget("text"),
            "Ready",
        )

        items = panel.risk_approval_steps.get(0, tk.END)

        self.assertEqual(len(items), 1)
        self.assertIn("step-002", items[0])


if __name__ == "__main__":
    unittest.main()
