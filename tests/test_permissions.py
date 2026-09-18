import unittest

from permissions.reporting import (
    ApprovalStatus,
    OperationRecord,
    PermissionRiskReport,
    RiskLevel,
)


class PermissionRiskTests(unittest.TestCase):
    def test_risk_levels_are_explicit(self) -> None:
        self.assertEqual(
            [RiskLevel.SAFE.value, RiskLevel.NOTABLE.value, RiskLevel.HIGH_RISK.value],
            ["SAFE", "NOTABLE", "HIGH_RISK"],
        )

    def test_approval_states_are_explicit(self) -> None:
        self.assertEqual(
            [
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.DENIED.value,
                ApprovalStatus.NOT_REQUESTED.value,
                ApprovalStatus.BLOCKED.value,
            ],
            ["APPROVED", "DENIED", "NOT_REQUESTED", "BLOCKED"],
        )

    def test_operation_record_is_immutable_and_supports_context(self) -> None:
        record = OperationRecord(
            "read file",
            RiskLevel.SAFE,
            ApprovalStatus.NOT_REQUESTED,
            "project-relative target",
        )

        self.assertEqual(record.operation, "read file")
        self.assertEqual(record.context, "project-relative target")
        with self.assertRaises(AttributeError):
            record.operation = "write file"

    def test_multiple_operations_preserve_insertion_order(self) -> None:
        report = PermissionRiskReport()
        records = [
            OperationRecord("first", RiskLevel.SAFE, ApprovalStatus.APPROVED),
            OperationRecord("second", RiskLevel.NOTABLE, ApprovalStatus.DENIED),
        ]

        for record in records:
            report.add(record)

        self.assertEqual(report.records, tuple(records))

    def test_empty_report_is_clean_and_deterministic(self) -> None:
        report = PermissionRiskReport()

        expected = (
            "PERMISSION / RISK SUMMARY\n\n"
            "Approvals requested:\n"
            "- None\n"
            "Permission status:\n"
            "- All requested permissions resolved\n"
            "Rollback:\n"
            "- Not recommended"
        )
        self.assertEqual(report.render(), expected)

    def test_mixed_risk_report_uses_distinct_sections(self) -> None:
        report = PermissionRiskReport()
        report.add(OperationRecord("inspect", RiskLevel.SAFE, ApprovalStatus.NOT_REQUESTED))
        report.add(
            OperationRecord(
                "write file",
                RiskLevel.NOTABLE,
                ApprovalStatus.APPROVED,
                "explicit target",
            )
        )
        report.add(OperationRecord("restore snapshot", RiskLevel.HIGH_RISK, ApprovalStatus.APPROVED))

        rendered = report.render()

        self.assertIn("🟢 Safe operations:\n- inspect", rendered)
        self.assertIn("🟡 Approved / notable operations:\n- write file: explicit target", rendered)
        self.assertIn("🔴 High-risk operations:\n- restore snapshot", rendered)

    def test_approved_and_denied_operations_are_reported_explicitly(self) -> None:
        report = PermissionRiskReport()
        report.add(OperationRecord("safe read", RiskLevel.SAFE, ApprovalStatus.APPROVED))
        report.add(OperationRecord("blocked write", RiskLevel.NOTABLE, ApprovalStatus.DENIED))

        rendered = report.render()

        self.assertIn("- safe read → APPROVED", rendered)
        self.assertIn("- blocked write → DENIED", rendered)
        self.assertIn("- Unresolved permissions remain", rendered)

    def test_blocked_operation_is_not_reported_as_successful(self) -> None:
        report = PermissionRiskReport()
        report.add(OperationRecord("execute command", RiskLevel.HIGH_RISK, ApprovalStatus.BLOCKED))

        rendered = report.render()

        self.assertIn("- execute command → BLOCKED", rendered)
        self.assertNotIn("execute command → APPROVED", rendered)
        self.assertIn("- Unresolved permissions remain", rendered)

    def test_rendering_is_deterministic(self) -> None:
        report = PermissionRiskReport()
        report.add(OperationRecord("alpha", RiskLevel.SAFE, ApprovalStatus.APPROVED))
        report.add(OperationRecord("beta", RiskLevel.HIGH_RISK, ApprovalStatus.NOT_REQUESTED))

        self.assertEqual(report.render("Not recommended - no rollback requested"), report.render("Not recommended - no rollback requested"))

    def test_rollback_status_is_represented(self) -> None:
        report = PermissionRiskReport()

        self.assertIn("- Recommended - review required", report.render("Recommended - review required"))


if __name__ == "__main__":
    unittest.main()
