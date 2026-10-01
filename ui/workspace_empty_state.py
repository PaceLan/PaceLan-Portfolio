"""Quiet, local ambient treatment for an empty Workspace viewer."""

from __future__ import annotations

from math import cos, pi
import time
import tkinter as tk

from ui.animation_accessibility import AnimationAccessibility


class WorkspaceEmptyState(tk.Canvas):
    """Show project-aware empty-state copy over a restrained cool backdrop."""

    _TOP = "#101521"
    _MID = "#17182C"
    _BOTTOM = "#10151F"
    _TEXT = "#D8DEEB"
    _MUTED = "#7F8BA7"
    _ACCENT = "#7485C7"

    def __init__(
        self,
        parent,
        accessibility: AnimationAccessibility | None = None,
    ) -> None:
        super().__init__(
            parent,
            background=self._TOP,
            highlightthickness=0,
            borderwidth=0,
            takefocus=0,
        )
        self._project_open = False
        self._agent_active = False
        self.accessibility = accessibility or AnimationAccessibility()
        self._ambient_started = time.monotonic()
        self._ambient_after = None
        self._caption_item = None
        self.bind("<Configure>", self._draw)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._draw()
        self._schedule_ambient()

    def set_project_open(self, project_open: bool) -> None:
        if self._project_open == project_open:
            return
        self._project_open = project_open
        self._draw()

    def set_agent_active(self, active: bool) -> None:
        if self._agent_active == active:
            return
        self._agent_active = active
        if active:
            self._cancel_ambient()
            if self._caption_item is not None:
                self.itemconfigure(self._caption_item, fill=self._MUTED)
        else:
            self._ambient_started = time.monotonic()
            self._schedule_ambient()

    def _draw(self, _event=None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 2 or height < 2:
            return

        self.delete("all")
        self._caption_item = None
        band_count = min(max(height // 8, 20), 72)
        for index in range(band_count):
            top = index / band_count
            bottom = (index + 1) / band_count
            color = self._background_color((top + bottom) / 2)
            self.create_rectangle(
                0,
                int(height * top),
                width,
                int(height * bottom) + 1,
                fill=color,
                outline=color,
            )

        self.create_line(
            width * 0.12,
            height * 0.39,
            width * 0.88,
            height * 0.39,
            fill="#20253A",
            width=1,
        )
        self.create_text(
            width / 2,
            height * 0.44,
            text="PACEPILOT  /  WORKSPACE",
            fill=self._MUTED,
            font=("TkDefaultFont", 9, "bold"),
        )
        self.create_text(
            width / 2,
            height * 0.51,
            text=(
                "No file selected"
                if self._project_open
                else "Open a project to begin"
            ),
            fill=self._TEXT,
            font=("TkDefaultFont", 17, "normal"),
        )
        self._caption_item = self.create_text(
            width / 2,
            height * 0.58,
            text=(
                "Select a file in the project tree to inspect it."
                if self._project_open
                else "Your project workspace will appear here."
            ),
            fill=self._MUTED,
            font=("TkDefaultFont", 10, "normal"),
        )

    def _background_color(self, position: float) -> str:
        if position < 0.5:
            return _mix_color(self._TOP, self._MID, position * 2)
        return _mix_color(self._MID, self._BOTTOM, (position - 0.5) * 2)

    def _schedule_ambient(self) -> None:
        if (
            self._agent_active
            or self.accessibility.reduced_motion
            or self._ambient_after is not None
        ):
            return
        self._ambient_after = self.after(240, self._animate_ambient)

    def _animate_ambient(self) -> None:
        self._ambient_after = None
        if self._agent_active or self._caption_item is None:
            return
        phase = (time.monotonic() - self._ambient_started) / 12.0
        pulse = (1 - cos(2 * pi * phase)) / 2
        self.itemconfigure(
            self._caption_item,
            fill=_mix_color(self._MUTED, self._ACCENT, pulse * 0.35),
        )
        self._schedule_ambient()

    def _cancel_ambient(self) -> None:
        if self._ambient_after is None:
            return
        try:
            self.after_cancel(self._ambient_after)
        except tk.TclError:
            pass
        self._ambient_after = None

    def _on_destroy(self, event) -> None:
        if event.widget is self:
            self._cancel_ambient()


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
