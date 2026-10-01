"""Throttled, reduced-motion-aware pointer response for UI surfaces only."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from typing import Callable

from ui.animation_accessibility import AnimationAccessibility


PointerCallback = Callable[[int, int, float], None]


@dataclass(frozen=True)
class PointerVisualPolicy:
    throttle_ms: int = 64
    fade_ms: int = 240
    max_intensity: float = 0.22
    decay: float = 0.58

    def __post_init__(self) -> None:
        if self.throttle_ms < 32:
            raise ValueError("pointer throttle must be at least 32ms")
        if self.fade_ms < self.throttle_ms:
            raise ValueError("pointer fade must not be shorter than throttle")
        if not 0 < self.max_intensity <= 0.3:
            raise ValueError("pointer intensity must remain subtle")
        if not 0 < self.decay < 1:
            raise ValueError("pointer decay must be between zero and one")


@dataclass(frozen=True)
class _Surface:
    widget: tk.Misc
    callback: PointerCallback


@dataclass
class _FadingSurface:
    surface: _Surface
    x: int
    y: int
    intensity: float


class PointerVisualLayer:
    """One application-level pointer policy shared by registered surfaces."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        accessibility: AnimationAccessibility | None = None,
        policy: PointerVisualPolicy | None = None,
    ) -> None:
        self.root = root
        self.accessibility = accessibility or AnimationAccessibility()
        self.policy = policy or PointerVisualPolicy()
        self.enabled = not self.accessibility.reduced_motion
        self.focused = True
        self._surfaces: dict[str, _Surface] = {}
        self._current: _Surface | None = None
        self._pending: tuple[_Surface | None, int, int] | None = None
        self._fading: list[_FadingSurface] = []
        self._after_id = None
        self._destroyed = False

        if self.enabled:
            self.root.bind_all("<Motion>", self._on_motion, add="+")
            self.root.bind_all("<Leave>", self._on_leave, add="+")
            self.root.bind("<FocusOut>", self._on_focus_out, add="+")
            self.root.bind("<FocusIn>", self._on_focus_in, add="+")
        self.root.bind("<Destroy>", self._on_destroy, add="+")

    def register(self, widget: tk.Misc, callback: PointerCallback) -> None:
        if not callable(callback):
            raise TypeError("pointer callback must be callable")
        self._surfaces[str(widget)] = _Surface(widget, callback)
        if widget.winfo_class() == "TButton":
            widget.bind("<Motion>", self._on_motion, add="+")

    def _on_motion(self, event: tk.Event) -> None:
        if not self.enabled or not self.focused or self._destroyed:
            return
        surface = self._find_surface(event.widget)
        if surface is None:
            self._pending = (None, 0, 0)
        else:
            try:
                local_x = int(event.x_root - surface.widget.winfo_rootx())
                local_y = int(event.y_root - surface.widget.winfo_rooty())
            except tk.TclError:
                return
            self._pending = (surface, local_x, local_y)
        self._schedule()

    def _on_leave(self, event: tk.Event) -> None:
        if not self.enabled or not self.focused or self._destroyed:
            return
        try:
            widget = self.root.winfo_containing(event.x_root, event.y_root)
        except tk.TclError:
            widget = None
        surface = self._find_surface(widget) if widget is not None else None
        if surface is None:
            self._pending = (None, 0, 0)
        else:
            self._pending = (
                surface,
                int(event.x_root - surface.widget.winfo_rootx()),
                int(event.y_root - surface.widget.winfo_rooty()),
            )
        self._schedule()

    def _on_focus_out(self, _event: tk.Event) -> None:
        self.focused = False
        self._cancel()
        self._clear_all()

    def _on_focus_in(self, _event: tk.Event) -> None:
        self.focused = True

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self.root:
            self._destroyed = True
            self._cancel()
            self._clear_all()

    def _find_surface(self, widget: tk.Misc | str) -> _Surface | None:
        current = widget
        if isinstance(current, str):
            try:
                current = self.root.nametowidget(current)
            except KeyError:
                return None
        while current is not None:
            surface = self._surfaces.get(str(current))
            if surface is not None:
                return surface
            current = getattr(current, "master", None)
        return None

    def _schedule(self) -> None:
        if self._after_id is None:
            self._after_id = self.root.after(
                self.policy.throttle_ms,
                self._flush,
            )

    def _flush(self) -> None:
        self._after_id = None
        if self._destroyed or not self.focused:
            return

        if self._pending is not None:
            surface, x, y = self._pending
            self._pending = None
            if self._current is not None and (
                surface is None or self._current.widget is not surface.widget
            ):
                self._fading.append(
                    _FadingSurface(
                        self._current,
                        x,
                        y,
                        self.policy.max_intensity,
                    )
                )
                self._current = None
            if surface is not None:
                self._current = surface
                surface.callback(x, y, self.policy.max_intensity)

        remaining: list[_FadingSurface] = []
        for fading in self._fading:
            fading.intensity *= self.policy.decay
            if fading.intensity < 0.015:
                fading.surface.callback(fading.x, fading.y, 0.0)
            else:
                fading.surface.callback(
                    fading.x,
                    fading.y,
                    fading.intensity,
                )
                remaining.append(fading)
        self._fading = remaining

        if self._fading or self._pending is not None:
            self._schedule()

    def _clear_all(self) -> None:
        if self._current is not None:
            try:
                self._current.callback(0, 0, 0.0)
            except tk.TclError:
                pass
        for fading in self._fading:
            try:
                fading.surface.callback(fading.x, fading.y, 0.0)
            except tk.TclError:
                pass
        self._current = None
        self._pending = None
        self._fading.clear()

    def _cancel(self) -> None:
        if self._after_id is None:
            return
        try:
            self.root.after_cancel(self._after_id)
        except tk.TclError:
            pass
        self._after_id = None


__all__ = ["PointerVisualLayer", "PointerVisualPolicy"]
