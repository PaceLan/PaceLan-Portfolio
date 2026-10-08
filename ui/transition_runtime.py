"""Tkinter runtime for rendering unified visual transitions."""

from __future__ import annotations

import time
import tkinter as tk
from typing import Callable, Optional

from ui.panel_transitions import TransitionPrimitive


class TransitionRuntime:
    """Drive time-based visual transition frames on the Tk event loop."""

    def __init__(
        self,
        root: tk.Misc,
        *,
        duration_ms: int = 180,
        frame_ms: int = 16,
        on_frame: Optional[Callable[[TransitionPrimitive, float], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        if duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if frame_ms <= 0:
            raise ValueError("frame_ms must be positive")

        self.root = root
        self.duration_ms = duration_ms
        self.frame_ms = frame_ms
        self.on_frame = on_frame
        self.on_complete = on_complete

        self._after_id = None
        self._primitive: Optional[TransitionPrimitive] = None
        self._started_at: Optional[float] = None
        self._running = False

        self.root.bind(
            "<Destroy>",
            self._on_destroy,
            add="+",
        )

    @property
    def running(self) -> bool:
        return self._running

    @property
    def primitive(self) -> Optional[TransitionPrimitive]:
        return self._primitive

    def start(self, primitive: TransitionPrimitive) -> None:
        self.stop()

        self._primitive = primitive
        self._started_at = time.perf_counter()
        self._running = True

        self._emit(0.0)

        if self.duration_ms == 0:
            self._finish()
            return

        self._schedule()

    def stop(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass

        self._after_id = None
        self._started_at = None
        self._running = False
        self._primitive = None

    def _schedule(self) -> None:
        if not self._running:
            return

        self._after_id = self.root.after(
            self.frame_ms,
            self._animate,
        )

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self.root:
            self.stop()

    def _animate(self) -> None:
        self._after_id = None

        if not self._running or self._started_at is None:
            return

        elapsed_ms = (
            time.perf_counter() - self._started_at
        ) * 1000.0

        progress = min(
            elapsed_ms / max(self.duration_ms, 1),
            1.0,
        )

        self._emit(self._ease(progress))

        if progress >= 1.0:
            self._finish()
            return

        self._schedule()

    def _emit(self, progress: float) -> None:
        if self._primitive is not None and self.on_frame is not None:
            self.on_frame(self._primitive, progress)

    def _finish(self) -> None:
        self._running = False
        self._after_id = None
        self._started_at = None

        primitive = self._primitive
        if primitive is not None and self.on_frame is not None:
            self.on_frame(primitive, 1.0)

        self._primitive = None

        if self.on_complete is not None:
            self.on_complete()

    @staticmethod
    def _ease(progress: float) -> float:
        progress = min(max(progress, 0.0), 1.0)
        return progress * progress * (3.0 - 2.0 * progress)


__all__ = ["TransitionRuntime"]
