from __future__ import annotations

from dataclasses import dataclass

from application.draft_input_authority import DraftInput
from application.models import ProjectGoal


@dataclass(frozen=True)
class GoalAnalysis:
    draft: DraftInput
    proposed_text: str
    suggestions: tuple[str, ...] = ()


@dataclass(frozen=True)
class GoalConfirmation:
    goal: ProjectGoal
    confirmed: bool


class GoalConfirmationFlow:
    """Converts non-authoritative draft input into an explicitly confirmed goal."""

    def analyze(
        self,
        draft: DraftInput,
        *,
        proposed_text: str | None = None,
        suggestions: tuple[str, ...] = (),
    ) -> GoalAnalysis:
        text = (
            proposed_text.strip()
            if proposed_text is not None
            else draft.content.strip()
        )
        if not text:
            raise ValueError("proposed goal must not be empty")

        return GoalAnalysis(
            draft=draft,
            proposed_text=text,
            suggestions=tuple(
                suggestion.strip()
                for suggestion in suggestions
                if suggestion.strip()
            ),
        )

    def revise(
        self,
        analysis: GoalAnalysis,
        *,
        revised_text: str | None = None,
        accepted_suggestions: tuple[str, ...] = (),
    ) -> GoalAnalysis:
        text = (
            revised_text.strip()
            if revised_text is not None
            else analysis.proposed_text.strip()
        )
        if not text:
            raise ValueError("revised goal must not be empty")

        accepted = tuple(
            suggestion.strip()
            for suggestion in accepted_suggestions
            if suggestion.strip()
        )

        return GoalAnalysis(
            draft=analysis.draft,
            proposed_text=text,
            suggestions=accepted,
        )

    def confirm(self, analysis: GoalAnalysis) -> GoalConfirmation:
        goal = ProjectGoal(text=analysis.proposed_text)

        return GoalConfirmation(
            goal=goal,
            confirmed=True,
        )
