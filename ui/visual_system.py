"""M25 Agent-stage focus and local visual-motion primitives."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import cos, pi
import time
import tkinter as tk
from tkinter import ttk

from ui.agent_state import AgentInteractionState
from ui.agent_transitions import (
    AgentStateTransitionMapper,
    AgentVisualState as WorkflowVisualState,
)
from ui.animation import AnimationKind, AnimationSpec
from ui.animation_accessibility import AnimationAccessibility
from ui.visual_tokens import DEFAULT_VISUAL_TOKENS, VisualTokens


class AgentStage(str, Enum):
    IDLE = "idle"
    TASK = "task"
    UNDERSTANDING = "understanding"
    PLAN = "plan"
    APPROVAL = "approval"
    EXECUTION = "execution"
    RESULT = "result"


class StageEffect(str, Enum):
    REST = "rest"
    IDLE = "idle"
    FOCUS = "focus"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    SUCCESS = "success"
    ERROR = "error"


@dataclass(frozen=True)
class AgentVisualProjection:
    stage: AgentStage
    workflow_state: WorkflowVisualState
    effect: StageEffect


@dataclass(frozen=True)
class AgentVisualTransition:
    source: AgentVisualProjection | None
    target: AgentVisualProjection
    animation: AnimationSpec


class AgentVisualSystem:
    """Project immutable Agent UI state into local stage emphasis."""

    _RUNNING = {"RUNNING", "IN_PROGRESS", "EXECUTING", "ACTIVE"}
    _WAITING = {
        "WAITING",
        "WAITING_APPROVAL",
        "PENDING_APPROVAL",
        "PAUSED",
        "BLOCKED",
    }
    _FAILED = {"FAILED", "FAILURE", "ERROR"}
    _SUCCEEDED = {"SUCCESS", "SUCCEEDED", "COMPLETED"}

    def __init__(
        self,
        accessibility: AnimationAccessibility | None = None,
    ) -> None:
        self.accessibility = accessibility or AnimationAccessibility()

    @classmethod
    def project(
        cls,
        state: AgentInteractionState,
    ) -> AgentVisualProjection:
        if not isinstance(state, AgentInteractionState):
            raise TypeError("state must be an AgentInteractionState")

        execution_status = cls._status(state.execution.status)
        result_status = cls._status(state.result.status)

        if execution_status in cls._FAILED or result_status in cls._FAILED:
            return AgentVisualProjection(
                AgentStage.RESULT,
                WorkflowVisualState.FAILED,
                StageEffect.ERROR,
            )

        if (
            execution_status in cls._SUCCEEDED
            or result_status in cls._SUCCEEDED
        ):
            return AgentVisualProjection(
                AgentStage.RESULT,
                WorkflowVisualState.COMPLETED,
                StageEffect.SUCCESS,
            )

        if (
            execution_status in cls._WAITING
            or (
                bool(state.risk_approval.steps)
                and not state.risk_approval.ready
            )
        ):
            return AgentVisualProjection(
                AgentStage.APPROVAL,
                WorkflowVisualState.WAITING_APPROVAL,
                StageEffect.WAITING,
            )

        if execution_status in cls._RUNNING:
            return AgentVisualProjection(
                AgentStage.EXECUTION,
                WorkflowVisualState.EXECUTING,
                StageEffect.RUNNING,
            )

        if state.plan.steps or state.plan.summary != "No plan available":
            return AgentVisualProjection(
                AgentStage.PLAN,
                WorkflowVisualState.PLAN_READY,
                (
                    StageEffect.READY
                    if state.risk_approval.ready
                    or cls._status(state.plan.status) == "READY"
                    else StageEffect.FOCUS
                ),
            )

        if (
            state.understanding.summary != "No understanding available"
            or state.understanding.relevant_files
            or state.understanding.relevant_symbols
        ):
            return AgentVisualProjection(
                AgentStage.UNDERSTANDING,
                WorkflowVisualState.UNDERSTANDING_READY,
                StageEffect.READY,
            )

        if (
            state.task.title != "No task"
            or state.task.description != "No task selected"
        ):
            return AgentVisualProjection(
                AgentStage.TASK,
                WorkflowVisualState.PROCESSING,
                (
                    StageEffect.READY
                    if cls._status(state.task.status) == "READY"
                    else StageEffect.FOCUS
                ),
            )

        return AgentVisualProjection(
            AgentStage.IDLE,
            WorkflowVisualState.IDLE,
            StageEffect.REST,
        )

    def transition(
        self,
        source: AgentVisualProjection | None,
        state: AgentInteractionState,
    ) -> AgentVisualTransition:
        target = self.project(state)
        source_state = (
            source.workflow_state
            if source is not None
            else WorkflowVisualState.IDLE
        )

        if source is not None and source == target:
            animation = AnimationSpec(AnimationKind.NONE, 0, 1)
        else:
            rule = AgentStateTransitionMapper.transition(
                source_state,
                target.workflow_state,
            )
            spec = (
                rule.animation.spec
                if rule is not None
                else AnimationSpec(AnimationKind.FADE, 360, 8)
            )
            animation = self.accessibility.adapt_spec(spec)

        return AgentVisualTransition(source, target, animation)

    @staticmethod
    def _status(value: str) -> str:
        return str(value).strip().replace(" ", "_").upper()


class _ColorFade:
    def __init__(self, widget, set_color, initial_color: str) -> None:
        self.widget = widget
        self.set_color = set_color
        self.color = initial_color
        self._after_id = None

    def to(self, color: str, spec: AnimationSpec) -> None:
        if color == self.color and self._after_id is None:
            return
        self._cancel()
        start = self.color
        if spec.kind is AnimationKind.NONE or spec.duration_ms <= 0:
            self.color = color
            self.set_color(color)
            return

        count = max(6, min(spec.steps, 12))
        duration = max(spec.duration_ms, 360)

        def frame(index: int) -> None:
            ratio = index / count
            current = _mix_color(start, color, ratio)
            self.color = current
            self.set_color(current)
            if index < count:
                self._after_id = self.widget.after(
                    max(30, duration // count),
                    lambda: frame(index + 1),
                )
            else:
                self._after_id = None

        frame(0)

    def _cancel(self) -> None:
        if self._after_id is None:
            return
        try:
            self.widget.after_cancel(self._after_id)
        except tk.TclError:
            pass
        self._after_id = None


class _StageOutline:
    def __init__(
        self,
        parent: ttk.Frame,
        background: str,
        tokens: VisualTokens = DEFAULT_VISUAL_TOKENS,
    ) -> None:
        self.parent = parent
        self.tokens = tokens
        colors = tokens.colors
        blue = colors.get("accent_blue", colors["accent"])
        purple = colors.get(
            "accent_purple",
            colors.get("agent_running", blue),
        )
        self._colors = {
            "blue": blue,
            "purple": purple,
            "ready": blue,
            "glow": _mix_color(background, purple, 0.42),
            "waiting_dim": _mix_color(background, purple, 0.22),
            "success": _mix_color(blue, purple, 0.55),
            "error": colors["error"],
        }
        self._theme_surface = self.tokens.colors["surface"]
        self._theme_border = self.tokens.colors["border"]
        self.canvas = tk.Canvas(
            parent,
            background=background,
            highlightthickness=0,
            borderwidth=0,
            takefocus=0,
        )
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.tk.call("lower", self.canvas._w)
        self.canvas.bind("<Configure>", self._draw)
        self.parent.bind("<Destroy>", self._on_destroy, add="+")
        self.effect = StageEffect.REST
        self.spec = AnimationSpec()
        self._after_id = None
        self._started = 0.0
        self._pointer_intensity = 0.0

    def apply_theme(self, palette) -> None:
        background = palette.surface_elevated
        self.canvas.configure(background=background)
        blue = palette.accent
        purple = palette.agent_running
        self._colors = {
            "blue": blue,
            "purple": purple,
            "ready": blue,
            "glow": _mix_color(background, purple, 0.42),
            "waiting_dim": _mix_color(background, purple, 0.22),
            "success": _mix_color(blue, purple, 0.55),
            "error": palette.error,
        }
        self._theme_surface = palette.surface
        self._theme_border = palette.border
        self._draw()

    def set_pointer(self, intensity: float) -> None:
        self._pointer_intensity = min(max(intensity, 0.0), 0.22)
        if self.effect not in {StageEffect.RUNNING, StageEffect.WAITING}:
            self._draw()

    def set_effect(self, effect: StageEffect, spec: AnimationSpec) -> None:
        if effect is self.effect:
            return
        self._cancel()
        self.effect = effect
        self.spec = spec
        self._started = time.monotonic()
        if effect in {StageEffect.REST, StageEffect.FOCUS, StageEffect.READY}:
            self._draw()
        elif spec.kind is AnimationKind.NONE:
            self._draw()
        else:
            self._tick()

    def _tick(self) -> None:
        self._draw()
        if self.effect in {
            StageEffect.IDLE,
            StageEffect.RUNNING,
            StageEffect.WAITING,
        }:
            self._after_id = self.parent.after(100, self._tick)
            return
        duration = max(self.spec.duration_ms, 650) / 1000
        if time.monotonic() - self._started < duration:
            self._after_id = self.parent.after(90, self._tick)
        else:
            self.effect = StageEffect.REST
            self._draw()
            self._after_id = None

    def _draw(self, _event=None) -> None:
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 8 or height < 8:
            return
        if (
            self.effect is StageEffect.REST
            and self._pointer_intensity <= 0.01
        ):
            return

        bounds = (1.5, 1.5, width - 1.5, height - 1.5)
        base = self._theme_border
        self.canvas.create_rectangle(*bounds, outline=base, width=1)

        if self.effect is StageEffect.REST:
            pointer_color = _mix_color(
                base,
                self._colors["blue"],
                self._pointer_intensity * 0.55,
            )
            self.canvas.create_rectangle(
                *bounds,
                outline=pointer_color,
                width=1,
            )
        elif self.effect is StageEffect.IDLE:
            phase = (time.monotonic() - self._started) / 18.0
            breath = (1 - cos(2 * pi * phase)) / 2
            color = _mix_color(
                base,
                self._colors["blue"],
                0.08 + breath * 0.10,
            )
            self.canvas.create_rectangle(
                *bounds,
                outline=color,
                width=1,
            )
        elif self.effect is StageEffect.RUNNING:
            self._draw_running_outline(width, height)
        elif self.effect is StageEffect.READY:
            self.canvas.create_rectangle(
                *bounds,
                outline=_mix_color(
                    self._theme_surface,
                    self._colors["blue"],
                    0.55,
                ),
                width=4,
            )
            self.canvas.create_rectangle(
                *bounds,
                outline=self._colors["ready"],
                width=1,
            )
        elif self.effect is StageEffect.WAITING:
            phase = (time.monotonic() - self._started) / 5.2
            breath = (1 - cos(2 * pi * phase)) / 2
            color = _mix_color(
                self._colors["waiting_dim"],
                self._colors["purple"],
                0.25 + breath * 0.55,
            )
            self.canvas.create_rectangle(
                *bounds,
                outline=color,
                width=2,
            )
        elif self.effect is StageEffect.SUCCESS:
            self._draw_fade(self._colors["success"])
        elif self.effect is StageEffect.ERROR:
            self._draw_fade(self._colors["error"])
        else:
            self.canvas.create_rectangle(
                *bounds,
                outline=self._colors["purple"],
                width=2,
            )

    def _draw_fade(self, color: str) -> None:
        duration = max(self.spec.duration_ms, 650) / 1000
        progress = min((time.monotonic() - self._started) / duration, 1.0)
        softened = _mix_color(
            color,
            self._theme_surface,
            progress,
        )
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.canvas.create_rectangle(
            1.5,
            1.5,
            width - 1.5,
            height - 1.5,
            outline=softened,
            width=2,
        )

    def _draw_running_outline(self, width: int, height: int) -> None:
        left = top = 2.0
        right = width - 2.0
        bottom = height - 2.0
        lengths = (right - left, bottom - top, right - left, bottom - top)
        perimeter = sum(lengths)
        if perimeter <= 0:
            return

        phase = ((time.monotonic() - self._started) % 7.5) / 7.5
        start = phase * perimeter
        span = perimeter * 0.17
        points = [
            self._point_on_outline(
                (start + span * index / 18) % perimeter,
                left,
                top,
                right,
                bottom,
                lengths,
            )
            for index in range(19)
        ]
        coordinates = [coordinate for point in points for coordinate in point]
        self.canvas.create_line(
            *coordinates,
            fill=self._colors["glow"],
            width=6,
            capstyle=tk.ROUND,
        )
        for index, (start_point, end_point) in enumerate(
            zip(points, points[1:])
        ):
            color = _mix_color(
                self._colors["blue"],
                self._colors["purple"],
                index / max(len(points) - 2, 1),
            )
            self.canvas.create_line(
                *start_point,
                *end_point,
                fill=color,
                width=2,
                capstyle=tk.ROUND,
            )

    @staticmethod
    def _point_on_outline(distance, left, top, right, bottom, lengths):
        edges = (
            (left, top, right, top),
            (right, top, right, bottom),
            (right, bottom, left, bottom),
            (left, bottom, left, top),
        )
        remaining = distance
        for edge, length in zip(edges, lengths):
            if remaining <= length:
                start_x, start_y, end_x, end_y = edge
                ratio = remaining / length if length else 0
                return (
                    start_x + (end_x - start_x) * ratio,
                    start_y + (end_y - start_y) * ratio,
                )
            remaining -= length
        return left, top

    def _cancel(self) -> None:
        if self._after_id is None:
            return
        try:
            self.parent.after_cancel(self._after_id)
        except tk.TclError:
            pass
        self._after_id = None

    def _on_destroy(self, event) -> None:
        if event.widget is self.parent:
            self._cancel()


class AgentPanelVisualSystem:
    """Apply M25 stage focus to only the currently active Agent region."""

    def __init__(
        self,
        root: tk.Misc,
        frames: dict[AgentStage, ttk.Frame],
        titles: dict[AgentStage, ttk.Label],
        *,
        tokens: VisualTokens = DEFAULT_VISUAL_TOKENS,
        accessibility: AnimationAccessibility | None = None,
    ) -> None:
        self.model = AgentVisualSystem(accessibility)
        self.style = ttk.Style(root)
        self.tokens = tokens
        self.colors = tokens.colors
        self.background = self.colors["surface_elevated"]
        self.muted = self.colors["text_muted"]
        self.focus = self.colors.get("accent_blue", self.colors["accent"])
        self.style.configure(
            "PacePilot.M25Stage.TFrame",
            background=self.background,
        )
        self.outlines: dict[AgentStage, _StageOutline] = {}
        self.title_fades: dict[AgentStage, _ColorFade] = {}
        self.idle_outline = _StageOutline(root, self.background, self.tokens)
        for stage, frame in frames.items():
            frame.configure(style="PacePilot.M25Stage.TFrame")
            self.outlines[stage] = _StageOutline(
                frame,
                self.background,
                self.tokens,
            )
        for stage, title in titles.items():
            style_name = f"PacePilot.M25Stage{id(title)}.TLabel"
            self.style.configure(
                style_name,
                background=self.background,
                foreground=self.muted,
            )
            title.configure(style=style_name)
            self.title_fades[stage] = _ColorFade(
                title,
                lambda color, name=style_name: self.style.configure(
                    name,
                    foreground=color,
                ),
                self.muted,
            )
        self.previous: AgentVisualProjection | None = None

    def apply_theme(self, palette) -> None:
        self.colors = {
            "background": palette.background,
            "surface": palette.surface,
            "surface_elevated": palette.surface_elevated,
            "text": palette.text,
            "text_muted": palette.text_muted,
            "border": palette.border,
            "accent": palette.accent,
            "agent_running": palette.agent_running,
            "success": palette.success,
            "error": palette.error,
        }
        self.background = palette.surface_elevated
        self.muted = palette.text_muted
        self.focus = palette.accent
        self.style.configure(
            "PacePilot.M25Stage.TFrame",
            background=self.background,
        )
        for outline in self.outlines.values():
            outline.apply_theme(palette)
        self.idle_outline.apply_theme(palette)
        for stage, title_fade in self.title_fades.items():
            style_name = f"PacePilot.M25Stage{id(title_fade.widget)}.TLabel"
            self.style.configure(
                style_name,
                background=self.background,
                foreground=self.muted,
            )
            title_fade.color = self.muted

    def render(self, state: AgentInteractionState) -> AgentVisualTransition:
        transition = self.model.transition(self.previous, state)
        target = transition.target
        self.idle_outline.set_effect(
            StageEffect.IDLE
            if target.stage is AgentStage.IDLE
            else StageEffect.REST,
            transition.animation,
        )
        for stage, outline in self.outlines.items():
            effect = (
                target.effect
                if stage is target.stage
                else StageEffect.REST
            )
            outline.set_effect(effect, transition.animation)

        title_color = (
            self.colors.get("agent_running", self.focus)
            if target.effect in {StageEffect.WAITING, StageEffect.SUCCESS}
            else self.focus
        )
        for stage, fade in self.title_fades.items():
            fade.to(
                title_color if stage is target.stage else self.muted,
                transition.animation,
            )

        self.previous = target
        return transition

    def set_pointer(self, stage: AgentStage, intensity: float) -> None:
        outline = self.outlines.get(stage)
        if outline is not None:
            outline.set_pointer(intensity)


def _mix_color(start: str, end: str, ratio: float) -> str:
    ratio = min(max(ratio, 0.0), 1.0)
    channels = tuple(
        round(
            int(start[index:index + 2], 16) * (1 - ratio)
            + int(end[index:index + 2], 16) * ratio
        )
        for index in (1, 3, 5)
    )
    return "#" + "".join(f"{channel:02X}" for channel in channels)


__all__ = [
    "AgentPanelVisualSystem",
    "AgentStage",
    "AgentVisualProjection",
    "AgentVisualSystem",
    "AgentVisualTransition",
    "StageEffect",
]
