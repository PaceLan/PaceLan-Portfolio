"""Quiet, local ambient treatment for an empty Workspace viewer."""

from __future__ import annotations

from math import cos, pi
import time
import tkinter as tk

from ui.animation_accessibility import AnimationAccessibility
from ui.visual_tokens import DEFAULT_VISUAL_TOKENS, VisualTokens


class WorkspaceEmptyState(tk.Canvas):
    """Show project-aware empty-state copy over a restrained cool backdrop."""

    def __init__(
        self,
        parent,
        accessibility: AnimationAccessibility | None = None,
        tokens: VisualTokens = DEFAULT_VISUAL_TOKENS,
    ) -> None:
        super().__init__(
            parent,
            background=tokens.colors["background"],
            highlightthickness=0,
            borderwidth=0,
            takefocus=0,
        )
        self._project_open = False
        self._agent_active = False
        self.accessibility = accessibility or AnimationAccessibility()
        self.colors = tokens.colors
        self.top_color = self.colors["background"]
        self.middle_color = _mix_color(
            self.colors["surface"],
            self.colors.get("accent_purple", self.colors["accent"]),
            0.10,
        )
        self.bottom_color = self.colors["surface"]
        self.text_color = self.colors["text"]
        self.muted_color = self.colors["text_muted"]
        self.accent_color = self.colors.get(
            "accent_blue",
            self.colors["accent"],
        )
        self._ambient_started = time.monotonic()
        self._ambient_after = None
        self._caption_item = None
        self._pointer_items: tuple[int, ...] | None = None
        self._pointer_x = 0
        self._pointer_y = 0
        self._pointer_intensity = 0.0
        self.bind("<Configure>", self._draw)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._draw()
        self._schedule_ambient()

    def apply_theme(self, palette) -> None:
        self.colors = {
            "background": palette.background,
            "surface": palette.surface,
            "surface_elevated": palette.surface_elevated,
            "text": palette.text,
            "text_muted": palette.text_muted,
            "border": palette.border,
            "accent": palette.accent,
        }
        self.top_color = palette.background
        self.middle_color = _mix_color(
            palette.surface,
            palette.agent_running,
            0.10,
        )
        self.bottom_color = palette.surface
        self.text_color = palette.text
        self.muted_color = palette.text_muted
        self.accent_color = palette.accent
        self.configure(background=palette.background)
        self._draw()

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
                self.itemconfigure(self._caption_item, fill=self.muted_color)
        else:
            self._ambient_started = time.monotonic()
            self._schedule_ambient()

    def set_pointer_visual(self, x: int, y: int, intensity: float) -> None:
        self._pointer_x = x
        self._pointer_y = y
        self._pointer_intensity = min(max(intensity, 0.0), 0.22)
        if self._pointer_items is None:
            self._draw()
            return
        self._update_pointer_items()

    def _draw(self, _event=None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 2 or height < 2:
            return

        self.delete("all")
        self._caption_item = None
        self._pointer_items = None
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

        self._create_pointer_items()

        self.create_line(
            width * 0.12,
            height * 0.39,
            width * 0.88,
            height * 0.39,
            fill=self.colors["border"],
            width=1,
        )
        self.create_text(
            width / 2,
            height * 0.44,
            text="PACEPILOT  /  WORKSPACE",
            fill=self.muted_color,
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
            fill=self.text_color,
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
            fill=self.muted_color,
            font=("TkDefaultFont", 10, "normal"),
        )

    def _background_color(self, position: float) -> str:
        if position < 0.5:
            return _mix_color(self.top_color, self.middle_color, position * 2)
        return _mix_color(
            self.middle_color,
            self.bottom_color,
            (position - 0.5) * 2,
        )

    def _create_pointer_items(self) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        radius_x = max(50, min(width * 0.24, 240))
        radius_y = max(45, min(height * 0.30, 180))
        background = self._background_color(
            self._pointer_y / max(height, 1)
        )
        ratios = (0.18, 0.11, 0.06)
        self._pointer_items = tuple(
            self.create_oval(
                0,
                0,
                0,
                0,
                fill=_mix_color(
                    background,
                    self.accent_color,
                    self._pointer_intensity * ratio,
                ),
                outline="",
                state=tk.HIDDEN,
                stipple=stipple,
            )
            for ratio, stipple in zip(ratios, ("gray12", "gray25", "gray50"))
        )
        self._update_pointer_items()

    def _update_pointer_items(self) -> None:
        if self._pointer_items is None:
            return
        width = self.winfo_width()
        height = self.winfo_height()
        radius_x = max(50, min(width * 0.24, 240))
        radius_y = max(45, min(height * 0.30, 180))
        position = self._pointer_y / max(height, 1)
        background = self._background_color(position)
        for index, ratio in enumerate((0.18, 0.11, 0.06)):
            item = self._pointer_items[index]
            self.coords(
                item,
                self._pointer_x - radius_x,
                self._pointer_y - radius_y,
                self._pointer_x + radius_x,
                self._pointer_y + radius_y,
            )
            color = _mix_color(
                background,
                self.accent_color,
                self._pointer_intensity * ratio,
            )
            self.itemconfigure(
                item,
                fill=color,
                state=(
                    tk.NORMAL
                    if self._pointer_intensity > 0.01
                    else tk.HIDDEN
                ),
            )

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
        if self._agent_active or self.accessibility.reduced_motion:
            return
        if self._caption_item is None:
            self._schedule_ambient()
            return
        phase = (time.monotonic() - self._ambient_started) / 12.0
        pulse = (1 - cos(2 * pi * phase)) / 2
        self.itemconfigure(
            self._caption_item,
            fill=_mix_color(self.muted_color, self.accent_color, pulse * 0.35),
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
