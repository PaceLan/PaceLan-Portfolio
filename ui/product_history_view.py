"""PacePilot product-growth history presentation."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .product_history import ProductHistory
from .visual_tokens import DEFAULT_VISUAL_TOKENS


class ProductHistoryView:
    """Present product-growth history as a standalone read-only view."""

    def __init__(
        self,
        parent,
        history: ProductHistory,
        *,
        tokens=None,
    ) -> None:
        self.parent = parent
        self.history = history
        self.tokens = tokens or DEFAULT_VISUAL_TOKENS

        self.frame = ttk.Frame(parent, padding=16)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        self.heading = ttk.Label(
            self.frame,
            text="PacePilot Growth History",
        )
        self.heading.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 12),
        )

        self.timeline = tk.Listbox(
            self.frame,
            activestyle="none",
            exportselection=False,
        )
        self.timeline.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self._render()

    def _render(self) -> None:
        self.timeline.delete(0, tk.END)

        for event in self.history.timeline():
            version = f" ? {event.version}" if event.version else ""
            self.timeline.insert(
                tk.END,
                f"{event.date} ? {event.title}{version}",
            )

    def refresh(self, history: ProductHistory) -> None:
        self.history = history
        self._render()

    def pack(self, **kwargs) -> None:
        self.frame.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)

    def destroy(self) -> None:
        self.frame.destroy()


__all__ = ["ProductHistoryView"]
