"""Deterministic permission and risk classification reporting."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class RiskLevel(str, Enum):
    """Risk categories for an operation."""

    SAFE = "SAFE"
    NOTABLE = "NOTABLE"
    HIGH_RISK = "HIGH_RISK"


class ApprovalStatus(str, Enum):
    """Explicit approval outcomes for an operation."""

    APPROVED = "APPROVED"
    DENIED = "DENIED"
    NOT_REQUESTED = "NOT_REQUESTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class OperationRecord:
    """An immutable classification record without enforcement behavior."""

    operation: str
    risk: RiskLevel
    approval: ApprovalStatus
    context: Optional[str] = None


class PermissionRiskReport:
    """Collect operation records and render a deterministic final summary."""

    def __init__(self) -> None:
        self._records: List[OperationRecord] = []

    def add(self, record: OperationRecord) -> None:
        """Add one explicit operation classification to the report."""
        self._records.append(record)

    @property
    def records(self) -> tuple[OperationRecord, ...]:
        """Return records in insertion order as an immutable view."""
        return tuple(self._records)

    def render(self, rollback: str = "Not recommended") -> str:
        """Render the standardized deterministic permission/risk summary."""
        lines = ["PERMISSION / RISK SUMMARY", ""]
        self._append_risk_section(lines, "🟢 Safe operations:", RiskLevel.SAFE)
        self._append_risk_section(lines, "🟡 Approved / notable operations:", RiskLevel.NOTABLE)
        self._append_risk_section(lines, "🔴 High-risk operations:", RiskLevel.HIGH_RISK)

        lines.append("Approvals requested:")
        if self._records:
            lines.extend(
                f"- {record.operation} → {record.approval.value}"
                for record in self._records
            )
        else:
            lines.append("- None")

        lines.extend(
            [
                "Permission status:",
                f"- {self._permission_status()}",
                "Rollback:",
                f"- {rollback}",
            ]
        )
        return "\n".join(lines)

    def _append_risk_section(
        self,
        lines: List[str],
        heading: str,
        risk: RiskLevel,
    ) -> None:
        records = [record for record in self._records if record.risk is risk]
        if not records:
            return
        lines.append(heading)
        for record in records:
            description = record.operation
            if record.context:
                description += f": {record.context}"
            lines.append(f"- {description}")

    def _permission_status(self) -> str:
        if any(
            record.approval in {ApprovalStatus.DENIED, ApprovalStatus.BLOCKED}
            for record in self._records
        ):
            return "Unresolved permissions remain"
        return "All requested permissions resolved"
