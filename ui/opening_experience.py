"""PacePilot M26.4 product opening experience."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from ui.theme import ThemeState



@dataclass(frozen=True)
class OpeningConfig:
    mark: str = "PacePilot"
    greeting: str = "Welcome back"
    duration_ms: int = 1800
    fade_in_ms: int = 520
    fade_out_ms: int = 420
    frame_ms: int = 40


class OpeningExperience:
    def __init__(
        self,
        root: tk.Tk,
        *,
        ambient=None,
        theme_state=None,
        config: OpeningConfig | None = None,
    ):
        self.root = root
        self.ambient = ambient
        self.theme_state = theme_state or ThemeState()
        self.config = config or OpeningConfig()

        self.completed = False
        self._started = False
        self._started_at = 0
        self._after_id = None

        self._overlay = tk.Frame(root, bd=0, highlightthickness=0)
        self._canvas = tk.Canvas(
            self._overlay,
            bd=0,
            highlightthickness=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", self._render)

    def set_greeting(self, greeting: str | None) -> None:
        self.config = OpeningConfig(
            mark=self.config.mark,
            greeting=greeting or "",
            duration_ms=self.config.duration_ms,
            fade_in_ms=self.config.fade_in_ms,
            fade_out_ms=self.config.fade_out_ms,
            frame_ms=self.config.frame_ms,
        )

    def start(self, on_complete=None) -> None:
        if self._started or self.completed:
            return

        self._started = True
        self._overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._overlay.lift()
        self._start_time = self.root.tk.call("clock", "milliseconds")
        self._animate(on_complete)

    def _animate(self, on_complete=None) -> None:
        if self.completed:
            return

        elapsed = self._elapsed_ms()

        if elapsed < self.config.fade_in_ms:
            progress = elapsed / max(self.config.fade_in_ms, 1)
        elif elapsed >= self.config.duration_ms - self.config.fade_out_ms:
            remaining = self.config.duration_ms - elapsed
            progress = max(0.0, remaining / max(self.config.fade_out_ms, 1))
        else:
            progress = 1.0

        self._render(progress, elapsed)

        if elapsed >= self.config.duration_ms:
            self.complete(on_complete)
            return

        self._after_id = self.root.after(self.config.frame_ms, lambda: self._animate(on_complete))

    def _elapsed_ms(self) -> int:
        return int(self.root.tk.call("clock", "milliseconds")) - self._start_time

    def _render(self, progress=1.0, elapsed=0) -> None:
        self._canvas.delete("all")

        palette = self.theme_state.palette if self.theme_state is not None else None
        self._canvas.configure(bg=palette.background)

        width = max(self._canvas.winfo_width(), 1)
        height = max(self._canvas.winfo_height(), 1)

        try:
            layers = self.ambient.snapshot(elapsed / 1000.0).layers
        except AttributeError:
            layers = ()

        for layer in layers:
            self._draw_ambient_layer(
                width,
                height,
                layer,
                elapsed,
            )

        pulse = 0.985 + 0.015 * min(max(progress, 0.0), 1.0)
        cx = width / 2
        cy = height / 2 - 12
        mark_size = max(20, int(30 * pulse))

        glow_ratio = min(max(progress, 0.0), 1.0)
        glow = self._mix_color(
            palette.background,
            palette.accent,
            0.22 * glow_ratio,
        )

        self._canvas.create_text(
            cx,
            cy,
            text=self.config.mark,
            fill=glow,
            font=("Segoe UI", mark_size, "bold"),
        )

        text_ratio = min(max(progress * 1.15, 0.0), 1.0)
        text_color = self._mix_color(
            palette.background,
            palette.text,
            text_ratio,
        )

        self._canvas.create_text(
            cx,
            cy + 48,
            text=self.config.greeting,
            fill=text_color,
            font=("Segoe UI", 12),
        )

    def _draw_ambient_layer(self, width, height, layer, elapsed) -> None:
        phase = (elapsed / max(layer.cycle_ms, 1)) * 6.283185307
        drift = layer.drift * 0.5

        x = layer.x + drift * __import__("math").sin(phase)
        y = layer.y + drift * __import__("math").cos(phase)

        radius = layer.radius
        rx = width * radius
        ry = height * radius

        color = layer.color
        opacity = max(0.0, min(layer.opacity, 1.0))
        steps = 5

        for index in range(steps, 0, -1):
            ratio = index / steps
            current = opacity * ratio * 0.22
            fill = self._blend_to_background(
                self.theme_state.palette.background,
                color,
                current,
            )
            self._canvas.create_oval(
                width * x - rx * ratio,
                height * y - ry * ratio,
                width * x + rx * ratio,
                height * y + ry * ratio,
                fill=fill,
                outline="",
            )

    @staticmethod
    def _blend_to_background(background: str, foreground: str, ratio: float) -> str:
        ratio = max(0.0, min(ratio, 1.0))
        return OpeningExperience._mix_color(background, foreground, ratio)

    @staticmethod
    def _mix_color(start: str, end: str, ratio: float) -> str:
        ratio = max(0.0, min(ratio, 1.0))
        channels = [
            round(
                int(start[index:index + 2], 16) * (1 - ratio)
                + int(end[index:index + 2], 16) * ratio
            )
            for index in (1, 3, 5)
        ]
        return "#" + "".join(f"{channel:02X}" for channel in channels)

    def complete(self, on_complete=None) -> None:
        if self.completed:
            return

        self.completed = True

        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

        self._overlay.destroy()

        if on_complete is not None:
            on_complete()


__all__ = ["OpeningConfig", "OpeningExperience"]
